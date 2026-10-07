"""Перевірки для реальних інструментів: openssl (сертифікати), qemu-img (образи), libvirt XML."""
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


def have(tool):
    return shutil.which(tool) is not None


def cert_info(path):
    """Розбирає сертифікат X.509 за допомогою openssl: CN, SAN, строк дії в днях, алгоритм ключа, самопідписаність."""
    p = subprocess.run(["openssl", "x509", "-in", str(path), "-noout", "-text"], capture_output=True, text=True)
    if p.returncode != 0:
        raise ValueError("openssl не зміг прочитати сертифікат: " + p.stderr.strip()[:200])
    t = p.stdout
    d = {}
    m = re.search(r"Subject:.*?CN\s*=\s*([^,\n]+)", t)
    d["cn"] = m.group(1).strip() if m else None
    sans = re.search(r"Subject Alternative Name:.*?\n\s+(.+)", t)
    d["sans"] = sorted(x.strip().replace("IP Address:", "IP:") for x in sans.group(1).split(",")) if sans else []
    nb = re.search(r"Not Before: (.+? GMT)", t).group(1)
    na = re.search(r"Not After : (.+? GMT)", t).group(1)
    f = "%b %d %H:%M:%S %Y GMT"
    d["days"] = round((datetime.strptime(na, f) - datetime.strptime(nb, f)).total_seconds() / 86400)
    alg = re.search(r"Public Key Algorithm: (\S+)", t)
    d["alg"] = alg.group(1) if alg else None
    bits = re.search(r"Public-Key: \((\d+) bit\)", t)
    d["bits"] = int(bits.group(1)) if bits else None
    curve = re.search(r"NIST CURVE: (\S+)", t) or re.search(r"ASN1 OID: (\S+)", t)
    d["curve"] = curve.group(1) if curve else None
    iss = re.search(r"Issuer:\s*(.+)", t).group(1).strip()
    sub = re.search(r"Subject:\s*(.+)", t).group(1).strip()
    d["self_signed"] = iss == sub
    d["ca"] = "CA:TRUE" in t
    return d


def qemu_info(path):
    p = subprocess.run(["qemu-img", "info", "--output=json", str(path)], capture_output=True, text=True)
    if p.returncode != 0:
        raise ValueError("qemu-img info: " + p.stderr.strip()[:200])
    return json.loads(p.stdout)


def xml_root(text):
    try:
        return ET.fromstring(text)
    except ET.ParseError as e:
        raise ValueError(f"XML не розбирається: {e}")


def virt_validate(path, kind):
    """virt-xml-validate (якщо встановлено): повертає (ok, повідомлення) або None, якщо інструмента немає."""
    if not have("virt-xml-validate"):
        return None
    p = subprocess.run(["virt-xml-validate", str(path), kind], capture_output=True, text=True)
    return p.returncode == 0, (p.stdout + p.stderr).strip()[:300]


KIB = {"KiB": 1, "MiB": 1024, "GiB": 1024 * 1024, "k": 1, "M": 1024, "G": 1024 * 1024, "b": 1 / 1024}


def memory_kib(el):
    unit = el.get("unit", "KiB")
    return int(float(el.text) * KIB[unit])


def domain_summary(text):
    r = xml_root(text)
    s = {"type": r.get("type"), "name": (r.findtext("name") or "").strip(), "memory_kib": memory_kib(r.find("memory")),
         "vcpus": int(r.findtext("vcpu").strip()), "os_type": None, "boot": [b.get("dev") for b in r.findall("./os/boot")],
         "disks": [], "nics": [], "machine": None}
    ot = r.find("./os/type")
    if ot is not None:
        s["os_type"], s["machine"] = ot.text, ot.get("machine")
    for d in r.findall("./devices/disk"):
        src = d.find("source")
        tgt = d.find("target")
        drv = d.find("driver")
        s["disks"].append(dict(device=d.get("device"), file=(src.get("file") or src.get("dev")) if src is not None else None,
                               dev=tgt.get("dev") if tgt is not None else None, bus=tgt.get("bus") if tgt is not None else None,
                               fmt=drv.get("type") if drv is not None else None, readonly=d.find("readonly") is not None))
    for i in r.findall("./devices/interface"):
        src = i.find("source")
        mdl = i.find("model")
        s["nics"].append(dict(type=i.get("type"), network=src.get("network") if src is not None else None,
                              bridge=src.get("bridge") if src is not None else None, model=mdl.get("type") if mdl is not None else None))
    return s


def network_summary(text):
    r = xml_root(text)
    ip = r.find("ip")
    rng = r.find("./ip/dhcp/range")
    fw = r.find("forward")
    br = r.find("bridge")
    return dict(name=(r.findtext("name") or "").strip(), forward=fw.get("mode") if fw is not None else None,
                bridge=br.get("name") if br is not None else None, address=ip.get("address") if ip is not None else None,
                netmask=ip.get("netmask") if ip is not None else None, prefix=ip.get("prefix") if ip is not None else None,
                dhcp_start=rng.get("start") if rng is not None else None, dhcp_end=rng.get("end") if rng is not None else None)

"""Перевірки LAB01 та МКР: keys.sh (справжній ssh-keygen), sshd-конфігурація, ufw.sh (модель фаєрвола)."""
import re
import shlex
import subprocess
import pytest
from harness import sandbox, sshdcfg, tooling, ufwsim
from . import _common


def check(V, case):
    kind = case["kind"]
    if kind == "keys":
        if not tooling.have("ssh-keygen"):
            pytest.skip("потрібен ssh-keygen (openssh-client)")
        res = sandbox.run_script(V.DIR / "keys.sh", case.get("args", []), case.get("files"), case.get("shims"), case.get("env"))
        errs = []
        try:
            errs += sandbox.check_case(res, case)
            if "SHA256:" in res.stdout or "+---" in res.stdout or "randomart" in res.stdout:
                errs.append("скрипт друкує відбиток або randomart ключа (використовуйте ssh-keygen -q); відбитки недетерміновані")
            ex = case.get("expect", {})
            for pub in ex.get("pubs", []):
                path = res.root / pub["path"]
                if not path.exists():
                    errs.append(f"немає {pub['path']}")
                    continue
                out = subprocess.run(["ssh-keygen", "-l", "-f", str(path)], capture_output=True, text=True).stdout
                m = re.match(r"(\d+) \S+ (.*) \((\w+)\)", out.strip())
                if not m:
                    errs.append(f"ssh-keygen -l не розібрав {pub['path']}: {out!r}")
                    continue
                bits, comment, typ = int(m.group(1)), m.group(2), m.group(3).lower()
                if "type" in pub and typ != pub["type"]:
                    errs.append(f"{pub['path']}: тип {typ}, очікувано {pub['type']}")
                if "bits" in pub and bits != pub["bits"]:
                    errs.append(f"{pub['path']}: біт {bits}, очікувано {pub['bits']}")
                if "comment" in pub and comment != pub["comment"]:
                    errs.append(f"{pub['path']}: коментар {comment!r}, очікувано {pub['comment']!r}")
                priv = res.root / pub["path"][:-4]
                if "priv_mode" in pub:
                    if not priv.exists():
                        errs.append(f"немає приватного ключа {pub['path'][:-4]}")
                    elif res.mode(pub["path"][:-4]) != pub["priv_mode"]:
                        errs.append(f"права {pub['path'][:-4]}: {oct(res.mode(pub['path'][:-4]))}, очікувано {oct(pub['priv_mode'])}")
                if "pub_mode" in pub and res.mode(pub["path"]) != pub["pub_mode"]:
                    errs.append(f"права {pub['path']}: {oct(res.mode(pub['path']))}, очікувано {oct(pub['pub_mode'])}")
                if "encrypted" in pub:
                    enc = b"ENCRYPTED" in priv.read_bytes() or b"aes" in priv.read_bytes()[:400]
                    out2 = subprocess.run(["ssh-keygen", "-y", "-P", "", "-f", str(priv)], capture_output=True, text=True)
                    protected = out2.returncode != 0
                    if protected != pub["encrypted"]:
                        errs.append(f"{pub['path'][:-4]}: захист парольною фразою {protected}, очікувано {pub['encrypted']}")
            ak = ex.get("authorized_keys")
            if ak:
                if not res.exists(ak["path"]):
                    errs.append(f"немає {ak['path']}")
                else:
                    lines = [l for l in res.read(ak["path"]).splitlines() if l.strip()]
                    if "count" in ak and len(lines) != ak["count"]:
                        errs.append(f"рядків у {ak['path']}: {len(lines)}, очікувано {ak['count']}")
                    for rx in ak.get("regex", []):
                        if not any(re.search(rx, l) for l in lines):
                            errs.append(f"жоден рядок {ak['path']} не відповідає /{rx}/: {lines!r}")
                    if "mode" in ak and res.mode(ak["path"]) != ak["mode"]:
                        errs.append(f"права {ak['path']}: {oct(res.mode(ak['path']))}, очікувано {oct(ak['mode'])}")
        finally:
            sandbox.cleanup(res)
    elif kind == "sshd":
        eff, errs = sshdcfg.effective((V.DIR / "sshd_hardening.conf").read_text(encoding="utf-8"))
        for k, want in case["expect"].items():
            got = eff.get(k.lower())
            if got != want:
                errs.append(f"{k}: очікувано {want}, отримано {got}")
    elif kind == "sshd_syntax":
        _, errs = sshdcfg.parse((V.DIR / "sshd_hardening.conf").read_text(encoding="utf-8"))
    elif kind in ("ufw", "ufw_state"):
        res = sandbox.run_script(V.DIR / "ufw.sh", [], None, {"ufw": "@ufw"}, None)
        try:
            if res.code != 0:
                errs = [f"ufw.sh завершився з кодом {res.code}: {res.stderr!r}"]
            else:
                try:
                    fw = ufwsim.from_log(res.shim_log("ufw"))
                except Exception as e:
                    fw, errs = None, [f"не вдалося розібрати команди ufw: {e}"]
                else:
                    errs = []
                    if kind == "ufw":
                        pk = case["packet"]
                        got = fw.decide(pk["proto"], pk["src"], pk["port"], pk.get("iface", "eth0"))
                        if got != case["expect"]:
                            errs.append(f"пакет {pk}: очікувано {case['expect']}, отримано {got}")
                    else:
                        if "enabled" in case and fw.enabled != case["enabled"]:
                            errs.append(f"enabled={fw.enabled}, очікувано {case['enabled']}")
                        if "default_in" in case and fw.default_in != case["default_in"]:
                            errs.append(f"default incoming={fw.default_in}, очікувано {case['default_in']}")
                        if "default_out" in case and fw.default_out != case["default_out"]:
                            errs.append(f"default outgoing={fw.default_out}, очікувано {case['default_out']}")
                        if "limit_rules" in case and sum(1 for r in fw.rules if r.action == "limit") != case["limit_rules"]:
                            errs.append(f"правил limit {sum(1 for r in fw.rules if r.action == 'limit')}, очікувано {case['limit_rules']}")
                        if "rules_count" in case and len(fw.rules) != case["rules_count"]:
                            errs.append(f"правил {len(fw.rules)}, очікувано {case['rules_count']}")
        finally:
            sandbox.cleanup(res)
    else:
        raise ValueError(kind)
    assert not errs, "\n".join(errs)

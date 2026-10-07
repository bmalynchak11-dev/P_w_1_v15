"""Перевірки LAB03 та МКР: vm.sh (справжній qemu-img), domain.xml і network.xml (розбір XML та virt-xml-validate)."""
import pytest
from harness import sandbox, tooling
from . import _common


def check(V, case):
    kind = case["kind"]
    errs = []
    if kind == "vm":
        if not tooling.have("qemu-img"):
            pytest.skip("потрібен qemu-img (qemu-utils)")
        res = sandbox.run_script(V.DIR / "vm.sh", case.get("args", []), case.get("files"), case.get("shims"), case.get("env"))
        try:
            res.stdout = "".join(l for l in res.stdout.splitlines(True) if not l.startswith(("Formatting '", "Image resized")))
            errs += sandbox.check_case(res, case)
            for rel, ex in (case.get("images") or {}).items():
                if not res.exists(rel):
                    errs.append(f"немає образу {rel}")
                    continue
                info = tooling.qemu_info(res.root / rel)
                got = {"format": info.get("format"), "virtual-size": info.get("virtual-size"),
                       "backing": info.get("backing-filename"), "backing-format": info.get("backing-filename-format")}
                for k in list(ex):
                    if k not in got:
                        got[k] = info.get(k)
                errs += _common.subset_errors(got, ex, rel)
        finally:
            sandbox.cleanup(res)
    elif kind in ("domain", "domain_valid"):
        text = (V.DIR / "domain.xml").read_text(encoding="utf-8")
        try:
            if kind == "domain":
                errs += _common.subset_errors(tooling.domain_summary(text), case["expect"], "domain")
            else:
                tooling.xml_root(text)
                v = tooling.virt_validate(V.DIR / "domain.xml", "domain")
                if v is None:
                    pytest.skip("потрібен virt-xml-validate (libvirt-clients)")
                if not v[0]:
                    errs.append("virt-xml-validate: " + v[1])
        except ValueError as e:
            errs.append(str(e))
    elif kind in ("network", "network_valid"):
        text = (V.DIR / "network.xml").read_text(encoding="utf-8")
        try:
            if kind == "network":
                errs += _common.subset_errors(tooling.network_summary(text), case["expect"], "network")
            else:
                tooling.xml_root(text)
                v = tooling.virt_validate(V.DIR / "network.xml", "network")
                if v is None:
                    pytest.skip("потрібен virt-xml-validate (libvirt-clients)")
                if not v[0]:
                    errs.append("virt-xml-validate: " + v[1])
        except ValueError as e:
            errs.append(str(e))
    else:
        raise ValueError(kind)
    assert not errs, "\n".join(errs)

"""Перевірки LAB02 та МКР: nginx.conf (модель маршрутизації) і tls.sh (справжній openssl)."""
import pytest
from harness import nginxsim, sandbox, tooling
from . import _common


def check(V, case):
    kind = case["kind"]
    if kind in ("nginx", "nginx_syntax", "nginx_headers", "nginx_upstream", "nginx_has"):
        cfg = nginxsim.Config((V.DIR / "nginx.conf").read_text(encoding="utf-8"))
        errs = list(cfg.errors)
        if kind == "nginx":
            r = cfg.route(case["scheme"], case["host"], case["path"], case.get("port"), case.get("client", "CLIENT"))
            ex = dict(case["expect"])
            if isinstance(ex.get("upstream"), str):
                ex["upstream"] = ex["upstream"].split("://", 1)[-1]
            errs += _common.subset_errors(r, ex, "відповідь")
        elif kind == "nginx_headers":
            h = cfg.headers_added(case["scheme"], case["host"], case["path"])
            errs += _common.subset_errors(h, case["expect"], "add_header")
        elif kind == "nginx_has":
            norm = " ".join((V.DIR / "nginx.conf").read_text(encoding="utf-8").split())
            for frag in case["contains"]:
                if " ".join(frag.split()) not in norm:
                    errs.append(f"у конфігурації немає фрагмента {frag!r}")
        elif kind == "nginx_upstream":
            errs += _common.subset_errors(cfg.upstreams, case["expect"], "upstream")
    elif kind == "tls":
        if not tooling.have("openssl"):
            pytest.skip("потрібен openssl")
        res = sandbox.run_script(V.DIR / "tls.sh", case.get("args", []), case.get("files"), case.get("shims"), case.get("env"))
        errs = []
        try:
            errs += sandbox.check_case(res, case)
            for item in case.get("certs", []):
                p = res.root / item["path"]
                if not p.exists():
                    errs.append(f"немає {item['path']}")
                    continue
                info = tooling.cert_info(p)
                exp = dict(item["expect"])
                exp["curve"] = {"prime256v1": "P-256", "secp384r1": "P-384", "secp521r1": "P-521"}.get(exp.get("curve"), exp.get("curve")) if "curve" in exp else None
                if "curve" not in item["expect"]:
                    exp.pop("curve")
                errs += _common.subset_errors(info, exp, item["path"])
            for path in res.root.rglob("*"):
                if path.is_file() and not path.relative_to(res.root).parts[0].startswith("_"):
                    head = path.read_bytes()[:64]
                    mode = path.stat().st_mode & 0o777
                    if b"PRIVATE KEY" in head and mode != 0o600:
                        errs.append(f"приватний ключ {path.relative_to(res.root)} має права {oct(mode)}, потрібно 0o600")
        finally:
            sandbox.cleanup(res)
    else:
        raise ValueError(kind)
    assert not errs, "\n".join(errs)

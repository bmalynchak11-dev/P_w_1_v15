"""Перевірки практичної P02 та МКР: pg_hba.conf, init.sql (привілеї), backup.sh."""
from harness import pgsim, sandbox
from . import _common


def check(V, case):
    kind = case["kind"]
    if kind == "hba":
        rules, errs = pgsim.parse_hba((V.DIR / "pg_hba.conf").read_text(encoding="utf-8"))
        if not errs:
            got = pgsim.hba_decision(rules, case["conn"], case["db"], case["user"], case.get("ip"), case.get("ssl", False), case.get("groups"))
            if got != case["expect"]:
                errs.append(f"{case['conn']} {case['user']}@{case['db']} з {case.get('ip')}: очікувано {case['expect']!r}, отримано {got!r}")
    elif kind == "hba_syntax":
        _, errs = pgsim.parse_hba((V.DIR / "pg_hba.conf").read_text(encoding="utf-8"))
    elif kind == "sql":
        c = pgsim.Cluster().run((V.DIR / "init.sql").read_text(encoding="utf-8"))
        errs = list(c.errors)
        for chk in case["checks"]:
            name, args, want = chk[0], chk[1:-1], chk[-1]
            got = getattr(c, name)(*args)
            if got != want:
                errs.append(f"{name}{tuple(args)}: очікувано {want}, отримано {got}")
    elif kind == "backup":
        res = sandbox.run_script(V.DIR / "backup.sh", case.get("args", []), case.get("files"), {"pg_dump": "@pg_dump", "pg_restore": "@pg_restore", **case.get("shims", {})},
                                 case.get("env"), case.get("stdin"), case.get("now", "2025-01-15 10:30:00"))
        try:
            errs = sandbox.check_case(res, case)
        finally:
            sandbox.cleanup(res)
    else:
        raise ValueError(kind)
    assert not errs, "\n".join(errs)

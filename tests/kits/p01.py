"""Перевірки практичної P01: Bash-скрипт + systemd service/timer."""
import pytest
from harness import sandbox, units


def check(V, case):
    kind = case["kind"]
    if kind == "script":
        res = sandbox.run_script(V.DIR / case.get("script", "task.sh"), case.get("args", []), case.get("files"), case.get("shims"),
                                 case.get("env"), case.get("stdin"), case.get("now", "2025-01-15 10:30:00"))
        try:
            errs = sandbox.check_case(res, case)
        finally:
            sandbox.cleanup(res)
    elif kind == "service":
        errs = units.unit_errors((V.DIR / "task.service").read_text(encoding="utf-8"), case.get("section", "Service"), case["expect"])
    elif kind == "timer":
        errs = units.unit_errors((V.DIR / "task.timer").read_text(encoding="utf-8"), case.get("section", "Timer"), case["expect"])
    elif kind == "calendar":
        errs = units.calendar_errors((V.DIR / "task.timer").read_text(encoding="utf-8"), case["start"], case["runs"])
    else:
        raise ValueError(kind)
    assert not errs, "\n".join(errs)

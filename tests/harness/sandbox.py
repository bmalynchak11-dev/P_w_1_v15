"""Пісочниця для запуску Bash-скриптів: тимчасова тека, файли-фікстури, підміна команд (shim) через PATH."""
import os
import shutil
import stat
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

FAKE_DATE = r'''#!/usr/bin/env python3
import os, re, sys
from datetime import datetime, timedelta
now = datetime.strptime(os.environ.get("FAKE_NOW", "2025-01-15 10:30:00"), "%Y-%m-%d %H:%M:%S")
args = sys.argv[1:]
fmt = None
when = now
i = 0
while i < len(args):
    a = args[i]
    if a.startswith("+"):
        fmt = a[1:]
    elif a in ("-d", "--date"):
        i += 1
        d = args[i].strip()
        m = re.fullmatch(r"(\d+)\s+(day|days|hour|hours|minute|minutes|week|weeks)\s+ago", d)
        if m:
            n, u = int(m.group(1)), m.group(2).rstrip("s")
            when = now - timedelta(**{u + "s": n})
        elif d == "yesterday":
            when = now - timedelta(days=1)
        elif d.startswith("@"):
            when = datetime.utcfromtimestamp(int(d[1:]))
        else:
            when = datetime.strptime(d, "%Y-%m-%d %H:%M:%S" if " " in d else "%Y-%m-%d")
    elif a in ("-u", "--utc", "-I"):
        pass
    i += 1
if fmt is None:
    print(when.strftime("%a %b %e %H:%M:%S UTC %Y"))
else:
    print(when.strftime(fmt.replace("%F", "%Y-%m-%d").replace("%T", "%H:%M:%S").replace("%s", str(int((when - datetime(1970, 1, 1)).total_seconds())))))
'''


PRESETS = {
    "ok": "exit 0",
    "fail": "exit 1",
    "pg_dump": """out=""; prev=""
for a in "$@"; do
  case $a in --file=*) out=${a#--file=};; esac
  if [ "$prev" = "-f" ] || [ "$prev" = "--file" ]; then out=$a; fi
  prev=$a
done
if [ -n "${FAIL_DUMP:-}" ]; then echo "pg_dump: error: connection to server failed" >&2; exit 1; fi
if [ -n "$out" ]; then echo "DUMP" > "$out"; else echo "DUMP"; fi""",
    "pg_restore": """if [ -n "${FAIL_RESTORE:-}" ]; then echo "pg_restore: error: unsupported version" >&2; exit 1; fi
for a in "$@"; do f=$a; done
if [ -f "$f" ] && grep -q DUMP "$f"; then echo "; Archive created"; echo "1; 0 0 TABLE DATA public t u"; exit 0; fi
echo "pg_restore: error: could not open input file" >&2; exit 1""",
    "pg_isready": """if [ -n "${DB_DOWN:-}" ]; then echo "no response"; exit 2; fi
echo "accepting connections"; exit 0""",
    "ufw": "exit 0",
    "sleep": "exit 0",
    "logger": "exit 0",
}


@dataclass
class Result:
    stdout: str
    stderr: str
    code: int
    root: Path
    calls: dict = field(default_factory=dict)

    def read(self, rel):
        return (self.root / rel).read_text(encoding="utf-8")

    def exists(self, rel):
        return (self.root / rel).exists()

    def listing(self, rel="."):
        p = self.root / rel
        hidden = {"_script.sh", "_shims", "_shimlog"}
        return sorted(x.name for x in p.iterdir() if x.name not in hidden) if p.is_dir() else []

    def mode(self, rel):
        return stat.S_IMODE((self.root / rel).stat().st_mode)

    def shim_log(self, name):
        p = self.root / "_shimlog" / f"{name}.log"
        return p.read_text(encoding="utf-8").splitlines() if p.exists() else []


def _write(root, rel, spec, now):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(spec, dict):
        text, mode, age = spec.get("text", ""), spec.get("mode"), spec.get("age_days")
    else:
        text, mode, age = spec, None, None
    if rel.endswith("/"):
        p.mkdir(parents=True, exist_ok=True)
        return
    p.write_text(text, encoding="utf-8")
    if mode is not None:
        p.chmod(mode)
    if age is not None:
        t = (now - timedelta(days=age)).timestamp()
        os.utime(p, (t, t))


def run_script(script, args=(), files=None, shims=None, env=None, stdin=None, fake_now="2025-01-15 10:30:00",
               interpreter="bash", timeout=20, cwd=None):
    """Запускає script у пісочниці.

    files: {відносний_шлях: текст | {"text":..., "mode":0o600, "age_days": N}}; шлях, що закінчується «/», створює порожню теку.
    shims: {ім'я_команди: текст Bash-скрипта}; кожен виклик shim дописує аргументи у _shimlog/<ім'я>.log.
    Команда date підміняється: показує fake_now (формат як у справжньої date: +формат, -d "N days ago").
    """
    root = Path(tempfile.mkdtemp(prefix="apsik-sb-"))
    try:
        now = datetime.now()
        for rel, spec in (files or {}).items():
            _write(root, rel, spec, now)
        bindir = root / "_shims"
        bindir.mkdir()
        (root / "_shimlog").mkdir()
        d = bindir / "date"
        d.write_text(FAKE_DATE)
        d.chmod(0o755)
        for name, body in (shims or {}).items():
            f = bindir / name
            if body.startswith("@"):
                body = PRESETS[body[1:]]
            f.write_text("#!/usr/bin/env bash\nprintf '%s\\n' \"$*\" >> \"" + str(root / "_shimlog" / f"{name}.log") + "\"\n" + body + "\n")
            f.chmod(0o755)
        e = dict(os.environ)
        e.update({"PATH": f"{bindir}:{e.get('PATH', '')}", "HOME": str(root), "LC_ALL": "C.UTF-8", "TZ": "UTC",
                  "FAKE_NOW": fake_now, "PYTHONDONTWRITEBYTECODE": "1"})
        for k in list(e):
            if k.startswith("VARIANT"):
                e.pop(k)
        e.update(env or {})
        sp = root / "_script.sh"
        shutil.copy(script, sp)
        sp.chmod(0o755)
        p = subprocess.run([interpreter, str(sp), *map(str, args)], input=stdin, text=True, capture_output=True,
                           cwd=str(cwd or root), env=e, timeout=timeout)
        return Result(p.stdout, p.stderr, p.returncode, root)
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise


def cleanup(res):
    shutil.rmtree(res.root, ignore_errors=True)


def check_case(res, case):
    """Порівнює результат із очікуваннями випадку (точні рядки)."""
    errors = []
    if "stdout" in case and res.stdout != case["stdout"]:
        errors.append(f"stdout:\n--- очікувано\n{case['stdout']!r}\n--- отримано\n{res.stdout!r}\n--- stderr\n{res.stderr!r}")
    if "stdout_lines" in case and sorted(res.stdout.splitlines()) != sorted(case["stdout_lines"]):
        errors.append(f"рядки stdout (без порядку): очікувано {sorted(case['stdout_lines'])!r}, отримано {sorted(res.stdout.splitlines())!r}")
    if "code" in case and res.code != case["code"]:
        errors.append(f"код завершення {res.code}, очікувано {case['code']}; stderr={res.stderr!r}")
    if "stderr_contains" in case and case["stderr_contains"] not in res.stderr:
        errors.append(f"stderr не містить {case['stderr_contains']!r}: {res.stderr!r}")
    for rel, content in (case.get("out_files") or {}).items():
        if not res.exists(rel):
            errors.append(f"немає файлу {rel}")
        elif res.read(rel) != content:
            errors.append(f"файл {rel}: очікувано {content!r}, отримано {res.read(rel)!r}")
    for rel in case.get("absent") or []:
        if res.exists(rel):
            errors.append(f"файл {rel} не мав існувати")
    for rel, names in (case.get("listing") or {}).items():
        if res.listing(rel) != sorted(names):
            errors.append(f"вміст {rel}: очікувано {sorted(names)}, отримано {res.listing(rel)}")
    sc = case.get("shim_calls") or {}
    if isinstance(sc, list):
        grouped = {}
        for line in sc:
            name, _, rest = line.partition(" ")
            grouped.setdefault(name, []).append(rest)
        sc = grouped
    for name, calls in sc.items():
        if res.shim_log(name) != calls:
            errors.append(f"виклики {name}: очікувано {calls}, отримано {res.shim_log(name)}")
    for rel, mode in (case.get("modes") or {}).items():
        if not res.exists(rel) or res.mode(rel) != mode:
            errors.append(f"права {rel}: очікувано {oct(mode)}, отримано {oct(res.mode(rel)) if res.exists(rel) else 'немає файлу'}")
    return errors

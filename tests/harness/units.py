"""Розбір unit-файлів systemd і спрощена модель OnCalendar (розклад запусків)."""
import re
from datetime import datetime, timedelta

DOWS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def parse_unit(text):
    """Повертає {секція: {ключ: [значення, ...]}} (ключі можуть повторюватися, \\ — продовження рядка)."""
    out, sec, buf = {}, None, ""
    for raw in text.splitlines():
        line = raw.strip()
        if buf:
            line = buf + " " + line
            buf = ""
        if not line or line[0] in "#;":
            continue
        if line.endswith("\\"):
            buf = line[:-1].strip()
            continue
        m = re.fullmatch(r"\[(\w+)\]", line)
        if m:
            sec = m.group(1)
            out.setdefault(sec, {})
            continue
        if "=" in line and sec:
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if v == "":
                out[sec][k] = []
            else:
                out[sec].setdefault(k, []).append(v)
    return out


def norm_ws(s):
    return re.sub(r"\s+", " ", s.strip())


def _expand(field, lo, hi):
    """Розкриває поле календаря: *, N, N,M, A..B, A/S, */S -> відсортований список."""
    res = set()
    for part in field.split(","):
        step = 1
        if "/" in part:
            part, st = part.split("/")
            step = int(st)
            start_only = part
        else:
            start_only = None
        if part == "*":
            a, b = lo, hi
        elif ".." in part:
            a, b = (int(x) for x in part.split(".."))
        else:
            a = int(part)
            b = hi if start_only is not None else a
        res.update(range(a, b + 1, step))
    return sorted(res)


def _dows(field):
    res = set()
    for part in field.lower().split(","):
        if ".." in part:
            a, b = part.split("..")
            ia, ib = DOWS.index(a[:3]), DOWS.index(b[:3])
            res.update(range(ia, ib + 1))
        else:
            res.add(DOWS.index(part[:3]))
    return res


def parse_calendar(expr):
    e = norm_ws(expr).lower()
    kw = {"minutely": "*-*-* *:*:00", "hourly": "*-*-* *:00:00", "daily": "*-*-* 00:00:00", "weekly": "mon *-*-* 00:00:00",
          "monthly": "*-*-01 00:00:00"}
    if e in kw:
        e = kw[e]
    dow, date, time = None, "*-*-*", None
    for tok in e.split():
        if re.fullmatch(r"[a-z]{3}[a-z,.]*", tok) and tok[:3] in DOWS:
            dow = _dows(tok)
        elif ":" in tok:
            time = tok
        elif "-" in tok:
            date = tok
        else:
            raise ValueError(f"непідтримуваний вираз OnCalendar: {expr!r}")
    if time is None:
        time = "00:00:00"
    if time.count(":") == 1:
        time += ":00"
    h, m, s = time.split(":")
    dparts = date.split("-")
    if len(dparts) != 3:
        raise ValueError(f"непідтримувана дата в OnCalendar: {expr!r}")
    y, mo, d = dparts
    return dict(dow=dow, year=None if y == "*" else _expand(y, 1970, 2200), month=_expand(mo, 1, 12), day=_expand(d, 1, 31),
                hours=_expand(h, 0, 23), minutes=_expand(m, 0, 59), seconds=_expand(s, 0, 59))


def next_runs(expr, start, count):
    """Перші count моментів після start ('YYYY-MM-DD HH:MM:SS')."""
    c = parse_calendar(expr)
    t0 = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
    out = []
    day = t0.replace(hour=0, minute=0, second=0)
    for _ in range(800):
        if (c["dow"] is None or day.weekday() in c["dow"]) and day.month in c["month"] and day.day in c["day"] \
                and (c["year"] is None or day.year in c["year"]):
            for h in c["hours"]:
                for mi in c["minutes"]:
                    for se in c["seconds"]:
                        t = day.replace(hour=h, minute=mi, second=se)
                        if t > t0:
                            out.append(t.strftime("%Y-%m-%d %H:%M:%S"))
                            if len(out) == count:
                                return out
        day += timedelta(days=1)
    return out


def unit_errors(text, section, expect):
    """expect: {ключ: [значення,...]} — точний збіг (з нормалізацією пробілів) списків значень ключа у секції."""
    u = parse_unit(text)
    errs = []
    if section not in u:
        return [f"немає секції [{section}]"]
    for k, vals in expect.items():
        got = [norm_ws(x) for x in u[section].get(k, [])]
        want = [norm_ws(x) for x in vals]
        if got != want:
            errs.append(f"[{section}] {k}: очікувано {want}, отримано {got}")
    return errs


def calendar_errors(text, start, expected_runs):
    u = parse_unit(text)
    vals = u.get("Timer", {}).get("OnCalendar", [])
    if len(vals) != 1:
        return [f"потрібен один рядок OnCalendar у [Timer], знайдено {len(vals)}"]
    try:
        got = next_runs(vals[0], start, len(expected_runs))
    except Exception as ex:
        return [f"OnCalendar={vals[0]!r} не вдалося розібрати: {ex}"]
    return [] if got == expected_runs else [f"OnCalendar={vals[0]!r}: від {start} очікувано {expected_runs}, отримано {got}"]

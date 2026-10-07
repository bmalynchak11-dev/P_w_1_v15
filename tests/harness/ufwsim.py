"""Модель UFW: розбір послідовності команд `ufw ...` і перевірка, що станеться з вхідним пакетом."""
import ipaddress
import re
import shlex

PROFILES = {"OpenSSH": [("tcp", 22, 22)], "Nginx HTTP": [("tcp", 80, 80)], "Nginx HTTPS": [("tcp", 443, 443)],
            "Nginx Full": [("tcp", 80, 80), ("tcp", 443, 443)], "Apache": [("tcp", 80, 80)], "Apache Secure": [("tcp", 443, 443)],
            "Apache Full": [("tcp", 80, 80), ("tcp", 443, 443)], "Postgresql": [("tcp", 5432, 5432)]}
ACTIONS = {"allow", "deny", "reject", "limit"}


class Rule:
    def __init__(self, action, direction="in", iface=None, proto=None, src=None, dst=None, ports=None, sport=None):
        self.action, self.direction, self.iface = action, direction, iface
        self.proto, self.src, self.dst, self.ports, self.sport = proto, src, dst, ports, sport  # ports: список (lo, hi) або None

    def key(self):
        return (self.action, self.direction, self.iface, self.proto, str(self.src), str(self.dst), tuple(self.ports or []), tuple(self.sport or []))

    def matches(self, direction, iface, proto, src, dport):
        if self.direction != direction:
            return False
        if self.iface and self.iface != iface:
            return False
        if self.proto and self.proto != proto:
            return False
        if self.src is not None and ipaddress.ip_address(src) not in self.src:
            return False
        if self.ports is not None and not any(lo <= dport <= hi for lo, hi in self.ports):
            return False
        return True


def _net(s):
    if s in ("any", "anywhere", "Anywhere"):
        return None
    return ipaddress.ip_network(s, strict=False)


def _ports(spec):
    out = []
    for part in spec.split(","):
        if ":" in part:
            a, b = part.split(":")
            out.append((int(a), int(b)))
        else:
            out.append((int(part), int(part)))
    return out


def parse_rule(tokens):
    """tokens після дії (allow/deny/…): [in|out] [on IF] [proto P] [from X] [to Y] [port N] або N[/proto] чи профіль."""
    t = list(tokens)
    r = Rule("?")
    direction, iface = "in", None
    if t and t[0] in ("in", "out"):
        direction = t.pop(0)
    if t and t[0] == "on":
        t.pop(0); iface = t.pop(0)
    if t and t[0] in ("in", "out"):
        direction = t.pop(0)
    r.direction, r.iface = direction, iface
    if not t:
        raise ValueError("порожнє правило")
    # коротка форма: 22/tcp, 80, 8000:8100/tcp, профіль
    first = " ".join(t)
    if first in PROFILES:
        r.ports = [(lo, hi) for _, lo, hi in PROFILES[first]]
        r.proto = PROFILES[first][0][0]
        return r
    if re.fullmatch(r"[\d:,]+(/(tcp|udp))?", t[0]) and len(t) == 1:
        spec, _, proto = t[0].partition("/")
        r.ports = _ports(spec); r.proto = proto or None
        return r
    i = 0
    while i < len(t):
        w = t[i]
        if w == "proto":
            r.proto = t[i + 1]; i += 2
        elif w == "from":
            r.src = _net(t[i + 1]); i += 2
            if i < len(t) and t[i] == "port":
                r.sport = _ports(t[i + 1]); i += 2
        elif w == "to":
            r.dst = _net(t[i + 1]); i += 2
            if i < len(t) and t[i] == "port":
                r.ports = _ports(t[i + 1]); i += 2
            elif i < len(t) and t[i] == "app":
                prof = PROFILES[t[i + 1]]; r.ports = [(lo, hi) for _, lo, hi in prof]; r.proto = r.proto or prof[0][0]; i += 2
        elif w == "port":
            r.ports = _ports(t[i + 1]); i += 2
        elif w == "app":
            prof = PROFILES[t[i + 1]]; r.ports = [(lo, hi) for _, lo, hi in prof]; r.proto = r.proto or prof[0][0]; i += 2
        elif w in ("log", "log-all", "comment"):
            i += 2 if w == "comment" else 1
        else:
            raise ValueError(f"невідомий елемент правила ufw: {w!r}")
    return r


class Firewall:
    def __init__(self):
        self.default_in, self.default_out = "deny", "allow"
        self.rules = []
        self.enabled = False
        self.errors = []

    def apply(self, argv):
        """argv — аргументи команди ufw (без слова ufw)."""
        a = [x for x in argv if x not in ("--force", "--dry-run")]
        if not a:
            return
        cmd = a[0]
        if cmd in ("enable", "disable", "reload", "reset", "status", "logging", "version", "show", "app"):
            if cmd == "enable":
                self.enabled = True
            if cmd == "disable":
                self.enabled = False
            if cmd == "reset":
                self.__init__()
            return
        if cmd == "default":
            pol, direction = a[1], a[2]
            if direction == "incoming":
                self.default_in = "deny" if pol in ("deny", "reject") else "allow"
            elif direction == "outgoing":
                self.default_out = "deny" if pol in ("deny", "reject") else "allow"
            return
        if cmd == "insert":
            n = int(a[1]); act = a[2]
            r = parse_rule(a[3:]); r.action = act
            self.rules.insert(n - 1, r)
            return
        if cmd == "delete":
            rest = a[1:]
            if rest and rest[0].isdigit():
                del self.rules[int(rest[0]) - 1]
                return
            act = rest[0]; r = parse_rule(rest[1:]); r.action = act
            self.rules = [x for x in self.rules if x.key() != r.key()]
            return
        if cmd in ACTIONS:
            r = parse_rule(a[1:]); r.action = cmd
            if not any(x.key() == r.key() for x in self.rules):
                self.rules.append(r)
            return
        raise ValueError(f"непідтримувана команда ufw: {' '.join(argv)}")

    def decide(self, proto, src, dport, iface="eth0", direction="in"):
        """Повертає 'ALLOW' або 'DENY' для нового вхідного з'єднання."""
        if not self.enabled:
            return "ALLOW"
        for r in self.rules:
            if r.matches(direction, iface, proto, src, dport):
                return "ALLOW" if r.action in ("allow", "limit") else "DENY"
        return "ALLOW" if self.default_in == "allow" else "DENY"


def from_log(lines):
    """lines — рядки журналу shim-команди ufw (аргументи через пробіл, можливі лапки)."""
    fw = Firewall()
    for ln in lines:
        fw.apply(shlex.split(ln))
    return fw

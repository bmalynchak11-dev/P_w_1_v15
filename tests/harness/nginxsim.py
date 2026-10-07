"""Спрощена модель Nginx: розбір конфігурації (контексти, директиви) і маршрутизація запиту до server/location."""
import re


def tokenize(text):
    toks, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
        elif c == "#":
            while i < n and text[i] != "\n":
                i += 1
        elif c in "{};":
            toks.append(c); i += 1
        elif c in "'\"":
            j = i + 1
            while j < n and text[j] != c:
                j += 2 if text[j] == "\\" else 1
            toks.append(text[i:j + 1]); i = j + 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in "{};":
                j += 1
            toks.append(text[i:j]); i = j
    return toks


def parse(text):
    """Повертає (дерево, помилки). Вузол: {'name', 'args', 'children': [...]|None}."""
    toks = tokenize(text)
    errors = []

    def block(i, top=False):
        out = []
        while i < len(toks):
            t = toks[i]
            if t == "}":
                if top:
                    errors.append("зайва «}»")
                    i += 1
                    continue
                return out, i + 1
            if t in "{;":
                errors.append(f"несподіваний {t!r}")
                i += 1
                continue
            name = t
            args = []
            i += 1
            while i < len(toks) and toks[i] not in "{;}":
                args.append(toks[i]); i += 1
            if i >= len(toks):
                errors.append(f"директива {name!r} без «;»")
                break
            if toks[i] == ";":
                out.append(dict(name=name, args=args, children=None)); i += 1
            elif toks[i] == "{":
                ch, i = block(i + 1)
                out.append(dict(name=name, args=args, children=ch))
            else:
                errors.append(f"директива {name!r} без «;» перед «}}»")
        if not top:
            errors.append("незакрита «{»")
        return out, i

    tree, _ = block(0, True)
    return tree, errors


def find(nodes, name):
    return [n for n in nodes if n["name"] == name]


def unq(s):
    return s[1:-1] if len(s) >= 2 and s[0] in "'\"" and s[-1] == s[0] else s


class Config:
    def __init__(self, text):
        self.tree, self.errors = parse(text)
        http = find(self.tree, "http")
        self.http = http[0]["children"] if http else []
        if not http:
            self.errors.append("немає блока http")
        self.upstreams = {}
        for u in find(self.http, "upstream"):
            self.upstreams[u["args"][0]] = [s["args"][0] for s in find(u["children"], "server")]
        self.servers = [s for s in find(self.http, "server")]
        if not find(self.tree, "events"):
            self.errors.append("немає блока events {} (без нього nginx не запуститься)")
        for srv in self.servers:
            if any("ssl" in d["args"] for d in find(srv["children"], "listen")):
                for need in ("ssl_certificate", "ssl_certificate_key"):
                    if not find(srv["children"], need):
                        self.errors.append(f"server з listen ... ssl без {need}")

    # --- вибір server
    def _listens(self, srv):
        res = []
        for d in find(srv["children"], "listen"):
            a = d["args"][0]
            ssl = "ssl" in d["args"]
            port = int(re.search(r"(\d+)$", a).group(1)) if re.search(r"\d+$", a) else 80
            res.append((port, ssl))
        return res or [(80, False)]

    def pick_server(self, port, host):
        cands = [s for s in self.servers if any(p == port for p, _ in self._listens(s))]
        if not cands:
            return None
        h = host.split(":")[0].lower()

        def names(s):
            return [unq(a).lower() for d in find(s["children"], "server_name") for a in d["args"]]
        for s in cands:                                  # точний збіг
            if h in names(s):
                return s
        best, blen = None, -1                            # *.example.com
        for s in cands:
            for nm in names(s):
                if nm.startswith("*.") and h.endswith(nm[1:]) and len(nm) > blen:
                    best, blen = s, len(nm)
        if best:
            return best
        for s in cands:                                  # регулярні ~
            for nm in names(s):
                if nm.startswith("~") and re.search(nm[1:], h):
                    return s
        for s in cands:                                  # default_server
            for p, _ in self._listens(s):
                pass
            for d in find(s["children"], "listen"):
                if "default_server" in d["args"] and int(re.search(r"(\d+)$", d["args"][0]).group(1)) == port:
                    return s
        return cands[0]

    # --- вибір location
    def pick_location(self, srv, path):
        locs = find(srv["children"], "location")
        exact, prefixes, regexes = [], [], []
        for l in locs:
            a = l["args"]
            if a[0] == "=":
                if path == a[1]:
                    return l
            elif a[0] == "^~":
                prefixes.append((a[1], True, l))
            elif a[0] in ("~", "~*"):
                regexes.append((a[1], a[0] == "~*", l))
            else:
                prefixes.append((a[0], False, l))
        best = None
        for pfx, stop, l in prefixes:
            if path.startswith(pfx) and (best is None or len(pfx) > len(best[0])):
                best = (pfx, stop, l)
        if best and best[1]:
            return best[2]
        for rx, ci, l in regexes:
            if re.search(rx, path, re.I if ci else 0):
                return l
        return best[2] if best else None

    def route(self, scheme, host, path, port=None, client="CLIENT"):
        self._client = client
        """Повертає опис результату: dict(kind=redirect|proxy|return|static|none, ...)."""
        port = port or (443 if scheme == "https" else 80)
        srv = self.pick_server(port, host)
        if srv is None:
            return dict(kind="none", reason="немає server")
        # server-рівневі директиви return/rewrite виконуються до location
        for d in srv["children"]:
            if d["name"] == "return":
                return self._ret(d, scheme, host, path)
        loc = self.pick_location(srv, path)
        if loc is None:
            root = find(srv["children"], "root")
            return dict(kind="static", root=root[0]["args"][0] if root else None, uri=path)
        ch = loc["children"]
        for d in ch:
            if d["name"] == "return":
                return self._ret(d, scheme, host, path)
        pp = find(ch, "proxy_pass")
        if pp:
            target = pp[0]["args"][0]
            m = re.match(r"https?://([^/]+)(/.*)?$", target)
            hostpart, uri = m.group(1), m.group(2)
            pfx = loc["args"][-1] if loc["args"][0] not in ("~", "~*") else None
            if uri is not None and pfx is not None and path.startswith(pfx):
                new_path = uri + path[len(pfx):]
            else:
                new_path = path
            hdrs = {}
            for h in find(ch, "proxy_set_header"):
                hdrs[h["args"][0]] = self._expand(unq(h["args"][1]), scheme, host, path) if len(h["args"]) > 1 else ""
            servers = self.upstreams.get(hostpart, [hostpart])
            return dict(kind="proxy", upstream=hostpart, servers=servers, path=new_path, headers=hdrs,
                        scheme=target.split(":")[0])
        root = find(ch, "root") or find(srv["children"], "root")
        alias = find(ch, "alias")
        return dict(kind="static", root=(root[0]["args"][0] if root else None), alias=(alias[0]["args"][0] if alias else None), uri=path)

    def _expand(self, v, scheme, host, path):
        return (v.replace("$host", host.split(":")[0]).replace("$scheme", scheme).replace("$remote_addr", getattr(self, "_client", "CLIENT"))
                .replace("$proxy_add_x_forwarded_for", getattr(self, "_client", "CLIENT")).replace("$request_uri", path).replace("$http_host", host))

    def _ret(self, d, scheme, host, path):
        a = d["args"]
        code = int(a[0]) if a[0].isdigit() else None
        if code in (301, 302, 307, 308) and len(a) > 1:
            return dict(kind="redirect", code=code, location=self._expand(unq(a[1]), scheme, host, path))
        return dict(kind="return", code=code, body=unq(a[1]) if len(a) > 1 else "")

    def headers_added(self, scheme, host, path):
        srv = self.pick_server(443 if scheme == "https" else 80, host)
        out = {}
        if srv:
            for d in find(srv["children"], "add_header"):
                out[d["args"][0]] = unq(d["args"][1])
        return out

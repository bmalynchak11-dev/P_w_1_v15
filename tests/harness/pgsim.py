"""Моделі PostgreSQL для перевірки без сервера: pg_hba.conf (перший збіг) і спрощений рушій привілеїв для init.sql."""
import ipaddress
import re


# ------------------------------------------------------------------ pg_hba.conf
def parse_hba(text):
    rules, errors = [], []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        t = line.split()
        typ = t[0]
        if typ == "local":
            if len(t) < 4:
                errors.append(f"рядок {n}: local потребує database user method")
                continue
            rules.append(dict(type="local", db=t[1], user=t[2], addr=None, method=t[3], line=n))
        elif typ in ("host", "hostssl", "hostnossl"):
            if len(t) < 5:
                errors.append(f"рядок {n}: {typ} потребує database user address method")
                continue
            addr = t[3]
            if "/" not in addr and addr not in ("all", "samehost", "samenet") and len(t) >= 6 and re.fullmatch(r"[\d.]+", t[4]):
                addr = f"{t[3]}/{t[4]}"; method = t[5]
            else:
                method = t[4]
            rules.append(dict(type=typ, db=t[1], user=t[2], addr=addr, method=method, line=n))
        else:
            errors.append(f"рядок {n}: невідомий тип запису {typ!r}")
    return rules, errors


def _list_match(spec, value, groups=None, db=None, user=None, kind="user"):
    for item in spec.split(","):
        if item == "all":
            return True
        if kind == "db":
            if item == "sameuser" and value == user:
                return True
            if item == value:
                return True
        else:
            if item.startswith("+"):
                if value in (groups or {}).get(item[1:], []):
                    return True
            elif item == value:
                return True
    return False


def hba_decision(rules, conn, db, user, ip=None, ssl=False, groups=None):
    """conn: 'local'|'host'. Повертає метод автентифікації з першого збігу або 'no-match'."""
    for r in rules:
        if conn == "local" and r["type"] != "local":
            continue
        if conn == "host":
            if r["type"] == "local":
                continue
            if r["type"] == "hostssl" and not ssl:
                continue
            if r["type"] == "hostnossl" and ssl:
                continue
            if r["addr"] != "all":
                if r["addr"] in ("samehost", "samenet"):
                    continue
                if ipaddress.ip_address(ip) not in ipaddress.ip_network(r["addr"], strict=False):
                    continue
        if not _list_match(r["db"], db, kind="db", user=user):
            continue
        if not _list_match(r["user"], user, groups=groups):
            continue
        return r["method"]
    return "no-match"


# ------------------------------------------------------------------ SQL-привілеї
class Cluster:
    def __init__(self):
        self.roles = {"postgres": dict(login=True, superuser=True, member_of=set())}
        self.dbs = {"postgres": dict(owner="postgres", acl={"PUBLIC": {"CONNECT", "TEMPORARY"}})}
        self.schemas = {}   # (db, schema) -> dict(owner, acl)
        self.tables = {}    # (db, schema, table) -> dict(owner, acl)
        self.defaults = []  # (db, schema, grantee, privs)
        self.cur = "postgres"
        self.errors = []
        self.add_schema("postgres", "public", "postgres", {"PUBLIC": {"USAGE"}})

    def add_schema(self, db, s, owner, acl=None):
        self.schemas[(db, s)] = dict(owner=owner, acl=acl or {})

    # --- виконання
    def run(self, sql):
        for stmt in split_sql(sql):
            try:
                self.exec(stmt)
            except Exception as e:  # noqa
                self.errors.append(f"{stmt[:60]!r}: {e}")
        return self

    def exec(self, st):
        s = re.sub(r"\s+", " ", st.strip())
        u = s.upper()
        m = re.match(r"\\(?:c|connect) (\S+)", s)
        if m:
            self.cur_db = m.group(1)
            return
        if not hasattr(self, "cur_db"):
            self.cur_db = "postgres"
        if u.startswith(("CREATE ROLE", "CREATE USER")):
            m = re.match(r"CREATE (?:ROLE|USER) (\"?[\w]+\"?)(.*)", s, re.I)
            name, opts = m.group(1).strip('"'), m.group(2)
            ou = opts.upper()
            login = ("NOLOGIN" not in ou) and (u.startswith("CREATE USER") or re.search(r"\bLOGIN\b", ou) is not None)
            mem = set()
            mm = re.search(r"IN ROLE ([\w, ]+?)(?: [A-Z]|$)", opts, re.I)
            if mm:
                mem = {x.strip() for x in mm.group(1).split(",")}
            self.roles[name] = dict(login=login, superuser="SUPERUSER" in ou and "NOSUPERUSER" not in ou, member_of=mem)
            return
        if u.startswith("ALTER ROLE") or u.startswith("ALTER USER"):
            m = re.match(r"ALTER (?:ROLE|USER) (\w+) (.*)", s, re.I)
            r = self.roles[m.group(1)]
            o = m.group(2).upper()
            if re.search(r"\bNOLOGIN\b", o):
                r["login"] = False
            elif re.search(r"\bLOGIN\b", o):
                r["login"] = True
            return
        if u.startswith("CREATE DATABASE"):
            m = re.match(r"CREATE DATABASE (\w+)(?: WITH)?(?: OWNER (?:=)?\s*(\w+))?", s, re.I)
            db = m.group(1)
            self.dbs[db] = dict(owner=m.group(2) or "postgres", acl={"PUBLIC": {"CONNECT", "TEMPORARY"}})
            self.add_schema(db, "public", "postgres", {"PUBLIC": {"USAGE"}})
            return
        if u.startswith("CREATE SCHEMA"):
            m = re.match(r"CREATE SCHEMA (?:IF NOT EXISTS )?(\w+)(?: AUTHORIZATION (\w+))?", s, re.I)
            self.add_schema(self.cur_db, m.group(1), m.group(2) or "postgres")
            return
        if u.startswith("CREATE TABLE"):
            m = re.match(r"CREATE TABLE (?:IF NOT EXISTS )?(?:(\w+)\.)?(\w+)", s, re.I)
            sch, t = m.group(1) or "public", m.group(2)
            key = (self.cur_db, sch, t)
            acl = {}
            for (db, ds, grantee, privs) in self.defaults:
                if db == self.cur_db and ds in (sch, None):
                    acl.setdefault(grantee, set()).update(privs)
            self.tables[key] = dict(owner="postgres", acl=acl)
            return
        if u.startswith("ALTER TABLE") and " OWNER TO " in u:
            m = re.match(r"ALTER TABLE (?:(\w+)\.)?(\w+) OWNER TO (\w+)", s, re.I)
            self.tables[(self.cur_db, m.group(1) or "public", m.group(2))]["owner"] = m.group(3)
            return
        if u.startswith("ALTER DEFAULT PRIVILEGES"):
            m = re.match(r"ALTER DEFAULT PRIVILEGES(?: IN SCHEMA (\w+))? GRANT (.+?) ON TABLES TO (\w+)", s, re.I)
            self.defaults.append((self.cur_db, m.group(1), m.group(3), expand_privs(m.group(2), "table")))
            return
        if u.startswith("GRANT ") and " TO " in u and " ON " not in u:
            m = re.match(r"GRANT (\w+) TO (\w+)", s, re.I)
            self.roles[m.group(2)]["member_of"].add(m.group(1))
            return
        if u.startswith(("GRANT ", "REVOKE ")):
            self.grant_revoke(s)
            return
        if u.startswith(("INSERT", "SELECT", "COMMENT", "SET ", "BEGIN", "COMMIT", "ALTER SYSTEM", "CREATE EXTENSION", "CREATE INDEX")):
            return
        raise ValueError("непідтримуваний оператор")

    def grant_revoke(self, s):
        m = re.match(r"(GRANT|REVOKE) (.+?) ON (.+?) (?:TO|FROM) (.+)", s, re.I)
        verb, privs, target, who = m.group(1).upper(), m.group(2), m.group(3), m.group(4)
        who = [w.strip().strip('"') for w in who.split(",")]
        who = ["PUBLIC" if w.upper() == "PUBLIC" else w for w in who]
        tu = target.upper()
        objs = []
        if tu.startswith("DATABASE "):
            names = [x.strip() for x in target[9:].split(",")]
            kind = "db"
            objs = [self.dbs[n]["acl"] for n in names]
        elif tu.startswith("SCHEMA "):
            kind = "schema"
            objs = [self.schemas[(self.cur_db, n.strip())]["acl"] for n in target[7:].split(",")]
        elif tu.startswith("ALL TABLES IN SCHEMA "):
            kind = "table"
            sch = target[len("ALL TABLES IN SCHEMA "):].strip()
            objs = [t["acl"] for (db, s_, _), t in self.tables.items() if db == self.cur_db and s_ == sch]
        else:
            kind = "table"
            tn = target[6:] if tu.startswith("TABLE ") else target
            for x in tn.split(","):
                x = x.strip()
                sch, _, t = x.rpartition(".")
                objs.append(self.tables[(self.cur_db, sch or "public", t)]["acl"])
        ps = expand_privs(privs, kind)
        for acl in objs:
            for w in who:
                if verb == "GRANT":
                    acl.setdefault(w, set()).update(ps)
                else:
                    acl.setdefault(w, set()).difference_update(ps)

    # --- запити
    def closure(self, role):
        seen, todo = {role, "PUBLIC"}, [role]
        while todo:
            r = todo.pop()
            for p in self.roles.get(r, {}).get("member_of", ()):
                if p not in seen:
                    seen.add(p); todo.append(p)
        return seen

    def _allowed(self, role, acl, owner, priv):
        if self.roles[role]["superuser"] or role == owner:
            return True
        return any(priv in acl.get(g, ()) for g in self.closure(role))

    def can_login(self, role):
        return role in self.roles and self.roles[role]["login"]

    def can_connect(self, role, db):
        return self.can_login(role) and db in self.dbs and self._allowed(role, self.dbs[db]["acl"], self.dbs[db]["owner"], "CONNECT")

    def schema_usage(self, role, db, sch="public"):
        s = self.schemas[(db, sch)]
        return self._allowed(role, s["acl"], s["owner"], "USAGE")

    def schema_create(self, role, db, sch="public"):
        s = self.schemas[(db, sch)]
        return self._allowed(role, s["acl"], s["owner"], "CREATE")

    def db_create(self, role, db):
        return self._allowed(role, self.dbs[db]["acl"], self.dbs[db]["owner"], "CREATE")

    def table_priv(self, role, db, table, priv, sch="public"):
        if "." in table:
            sch, table = table.split(".", 1)
        t = self.tables[(db, sch, table)]
        return self.schema_usage(role, db, sch) and self._allowed(role, t["acl"], t["owner"], priv.upper())

    def is_member(self, role, parent):
        return parent in self.closure(role)


def expand_privs(p, kind):
    p = p.strip().upper()
    full = {"db": {"CONNECT", "CREATE", "TEMPORARY"}, "schema": {"USAGE", "CREATE"},
            "table": {"SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"}}[kind]
    if p in ("ALL", "ALL PRIVILEGES"):
        return set(full)
    out = set()
    for x in p.split(","):
        x = x.strip()
        out.add("TEMPORARY" if x == "TEMP" else x)
    return out


def split_sql(sql):
    """Ділить на оператори за «;» поза лапками; рядки з \\c окремими операторами."""
    out, buf, q = [], "", None
    for line in sql.splitlines():
        ls = line.strip()
        if not buf.strip() and ls.startswith("\\"):
            out.append(ls)
            continue
        if not buf.strip() and (ls.startswith("--") or not ls):
            continue
        for ch in line:
            if q:
                buf += ch
                if ch == q:
                    q = None
            elif ch in "'\"":
                q = ch; buf += ch
            elif ch == ";":
                if buf.strip():
                    out.append(buf.strip())
                buf = ""
            else:
                buf += ch
        buf += "\n"
    if buf.strip():
        out.append(buf.strip())
    return out

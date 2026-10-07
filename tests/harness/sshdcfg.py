"""Ефективна конфігурація sshd за текстом sshd_config (перше значення виграє; AllowUsers/AllowGroups накопичуються)."""
KEYWORDS = {k.lower() for k in """AcceptEnv AddressFamily AllowAgentForwarding AllowGroups AllowStreamLocalForwarding AllowTcpForwarding AllowUsers
AuthenticationMethods AuthorizedKeysCommand AuthorizedKeysCommandUser AuthorizedKeysFile AuthorizedPrincipalsCommand AuthorizedPrincipalsFile Banner
CASignatureAlgorithms ChannelTimeout ChrootDirectory Ciphers ClientAliveCountMax ClientAliveInterval Compression DenyGroups DenyUsers DisableForwarding
ExposeAuthInfo FingerprintHash ForceCommand GatewayPorts GSSAPIAuthentication GSSAPICleanupCredentials HostbasedAuthentication
HostbasedAcceptedAlgorithms HostKey HostKeyAgent HostKeyAlgorithms IgnoreRhosts IgnoreUserKnownHosts Include IPQoS KbdInteractiveAuthentication
KerberosAuthentication KexAlgorithms ListenAddress LoginGraceTime LogLevel LogVerbose MACs Match MaxAuthTries MaxSessions MaxStartups ModuliFile
PasswordAuthentication PermitEmptyPasswords PermitListen PermitOpen PermitRootLogin PermitTTY PermitTunnel PermitUserEnvironment PermitUserRC PerSourceMaxStartups
PerSourceNetBlockSize PidFile Port PrintLastLog PrintMotd PubkeyAcceptedAlgorithms PubkeyAuthentication PubkeyAuthOptions RekeyLimit RequiredRSASize
RevokedKeys RDomain SecurityKeyProvider SetEnv StreamLocalBindMask StreamLocalBindUnlink StrictModes Subsystem SyslogFacility TCPKeepAlive TrustedUserCAKeys
UnusedConnectionTimeout UseDNS UsePAM VersionAddendum X11DisplayOffset X11Forwarding X11UseLocalhost XAuthLocation""".split()}
ACCUMULATE = {"allowusers", "allowgroups", "denyusers", "denygroups", "listenaddress", "port", "hostkey", "acceptenv", "subsystem"}
DEFAULTS = {"port": ["22"], "permitrootlogin": ["prohibit-password"], "passwordauthentication": ["yes"], "pubkeyauthentication": ["yes"],
            "maxauthtries": ["6"], "logingracetime": ["120"], "x11forwarding": ["no"], "allowtcpforwarding": ["yes"],
            "permitemptypasswords": ["no"], "clientaliveinterval": ["0"], "clientalivecountmax": ["3"], "maxsessions": ["10"],
            "usepam": ["yes"], "kbdinteractiveauthentication": ["no"], "loglevel": ["INFO"], "allowagentforwarding": ["yes"],
            "permittty": ["yes"], "strictmodes": ["yes"], "usedns": ["no"], "printmotd": ["no"], "maxstartups": ["10:30:100"]}


def parse(text):
    """Повертає (effective, errors): effective — {ключ_нижнім_регістром: [значення]}; секція Match ігнорується для ефективних значень."""
    eff, errors, in_match = {}, [], False
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.replace("=", " ", 1).split(None, 1) if "=" in line.split()[0] else line.split(None, 1)
        key = parts[0].lower()
        val = parts[1].strip() if len(parts) > 1 else ""
        if key not in KEYWORDS:
            errors.append(f"рядок {n}: невідома директива {parts[0]!r}")
            continue
        if not val and key != "match":
            errors.append(f"рядок {n}: директива {parts[0]} без значення")
            continue
        if key == "match":
            in_match = True
            continue
        if in_match:
            continue
        if key in ACCUMULATE:
            eff.setdefault(key, [])
            eff[key].extend(val.split() if key in ("allowusers", "allowgroups", "denyusers", "denygroups") else [val])
        elif key not in eff:
            eff[key] = [val]
    return eff, errors


def effective(text):
    eff, errors = parse(text)
    full = {k: list(v) for k, v in DEFAULTS.items()}
    full.update(eff)
    return full, errors

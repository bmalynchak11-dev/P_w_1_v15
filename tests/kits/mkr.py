"""МКР: диспетчер перевірок за видом (kind) завдання."""
from . import p01, p02, lab01, lab02, lab03

ROUTES = {}
for mod, kinds in ((p01, ("script", "service", "timer", "calendar")), (p02, ("hba", "hba_syntax", "sql", "backup")),
                   (lab01, ("keys", "sshd", "sshd_syntax", "ufw", "ufw_state")), (lab02, ("nginx", "nginx_syntax", "nginx_headers", "nginx_upstream", "nginx_has", "tls")),
                   (lab03, ("vm", "domain", "domain_valid", "network", "network_valid"))):
    for k in kinds:
        ROUTES[k] = mod


def check(V, case):
    ROUTES[case["kind"]].check(V, case)

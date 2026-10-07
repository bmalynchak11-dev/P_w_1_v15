"""Автоматична перевірка варіанта 21."""
import pytest
from conftest import load
from kits import p01

V = load(21)
CASES = [{'id': 'топ-3 служб',
  'public': True,
  'kind': 'script',
  'args': [],
  'shims': {'journalctl': "printf '%s\\n' 'Jan 15 09:00:01 srv1 sshd[411]: Accepted publickey for admin' "
                          "'Jan 15 09:00:05 srv1 cron[512]: (root) CMD (run-parts)' 'Jan 15 09:01:10 srv1 "
                          "sshd[413]: Failed password for root' 'Jan 15 09:02:00 srv1 kernel: eth0 link up' "
                          "'Jan 15 09:03:00 srv1 sshd[420]: Connection closed' 'Jan 15 09:04:00 srv1 "
                          "cron[515]: (root) CMD (backup)' 'Jan 15 09:05:00 srv1 nginx[600]: worker "
                          "started'"},
  'stdout': 'sshd 3\ncron 2\nkernel 1\nУсього: 7\n',
  'code': 0,
  'shim_calls': {'journalctl': ['-o short --no-pager']}},
 {'id': 'службові рядки пропускаються',
  'public': True,
  'kind': 'script',
  'args': [],
  'shims': {'journalctl': "printf '%s\\n' '-- Journal begins' 'Jan  5 08:00:00 vm2 chronyd[301]: Selected "
                          "source' 'Jan  5 08:10:00 vm2 chronyd[301]: System clock wrong' 'Jan  5 08:20:00 "
                          "vm2 systemd[1]: Started Daily cleanup' '-- Reboot --'"},
  'stdout': 'chronyd 2\nsystemd 1\nУсього: 3\n',
  'code': 0}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_21(case):
    p01.check(V, case)

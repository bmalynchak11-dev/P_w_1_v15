"""Автоматична перевірка варіанта 07."""
import pytest
from conftest import load
from kits import p01

V = load(7)
CASES = [{'id': 'одна неактивна служба',
  'public': True,
  'kind': 'script',
  'args': ['nginx', 'sshd'],
  'shims': {'systemctl': 'case "$*" in "is-active nginx") echo active;; "is-active sshd") echo inactive; '
                         'exit 3;; *) exit 4;; esac'},
  'stdout': 'nginx: active\nsshd: inactive\nНеактивних: 1\n',
  'code': 1,
  'shim_calls': {'systemctl': ['is-active nginx', 'is-active sshd']}},
 {'id': 'усі служби активні',
  'public': True,
  'kind': 'script',
  'args': ['nginx', 'cron'],
  'shims': {'systemctl': 'echo active'},
  'stdout': 'nginx: active\ncron: active\nНеактивних: 0\n',
  'code': 0}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_07(case):
    p01.check(V, case)

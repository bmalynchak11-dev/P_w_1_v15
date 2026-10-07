"""Автоматична перевірка варіанта 26."""
import pytest
from conftest import load
from kits import p01

V = load(26)
CASES = [{'id': 'два критичні рядки',
  'public': True,
  'kind': 'script',
  'args': ['journal.log', 'admin@example.org'],
  'files': {'journal.log': 'INFO service started\n'
                           'CRITICAL disk full on /dev/sda1\n'
                           'WARNING cpu at 85%\n'
                           'CRITICAL fan failure\n'},
  'shims': {'mail': '@ok'},
  'stdout': 'Надіслано: 2\n',
  'code': 0,
  'shim_calls': {'mail': ['-s CRITICAL: CRITICAL disk full on /dev/sda1 admin@example.org',
                          '-s CRITICAL: CRITICAL fan failure admin@example.org']}},
 {'id': 'збій mail',
  'public': True,
  'kind': 'script',
  'args': ['journal.log', 'admin@example.org'],
  'files': {'journal.log': 'CRITICAL fan failure\n'},
  'shims': {'mail': '@fail'},
  'stdout': 'Надіслано: 0\n',
  'code': 1,
  'stderr_contains': 'Помилка: лист не надіслано',
  'shim_calls': {'mail': ['-s CRITICAL: CRITICAL fan failure admin@example.org']}}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_26(case):
    p01.check(V, case)

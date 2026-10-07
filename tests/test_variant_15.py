"""Автоматична перевірка варіанта 15."""
import pytest
from conftest import load
from kits import p01

V = load(15)
CASES = [{'id': 'успішне дзеркалювання',
  'public': True,
  'kind': 'script',
  'args': ['src', 'mirror'],
  'files': {'src/a.txt': 'A'},
  'shims': {'rsync': '@ok'},
  'stdout': '',
  'code': 0,
  'shim_calls': {'rsync': ['-a --delete src/ mirror/']},
  'out_files': {'mirror.log': '2025-01-15 10:30 OK\n'}},
 {'id': 'помилка rsync',
  'public': True,
  'kind': 'script',
  'args': ['src', 'mirror'],
  'files': {'src/a.txt': 'A'},
  'shims': {'rsync': '@fail'},
  'stdout': '',
  'code': 1,
  'stderr_contains': 'Помилка: rsync завершився невдало',
  'shim_calls': {'rsync': ['-a --delete src/ mirror/']},
  'out_files': {'mirror.log': '2025-01-15 10:30 FAIL\n'}}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_15(case):
    p01.check(V, case)

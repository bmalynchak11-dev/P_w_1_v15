"""Автоматична перевірка варіанта 17."""
import pytest
from conftest import load
from kits import p01

V = load(17)
CASES = [{'id': 'звіт створюється',
  'public': True,
  'kind': 'script',
  'args': ['reps'],
  'files': {'reps/': ''},
  'now': '2025-01-15 10:30:00',
  'shims': {'hostname': 'echo server1', 'uname': 'echo 6.1.0', 'who': 'echo a\necho b'},
  'stdout': 'reps/report-20250115.txt\n',
  'code': 0,
  'out_files': {'reps/report-20250115.txt': 'host: server1\nkernel: 6.1.0\nusers: 2\n'}},
 {'id': 'нуль користувачів',
  'public': True,
  'kind': 'script',
  'args': ['out'],
  'files': {'out/': ''},
  'now': '2025-01-15 11:30:00',
  'shims': {'hostname': 'echo mx', 'uname': 'echo 5.15', 'who': ''},
  'stdout': 'out/report-20250115.txt\n',
  'code': 0,
  'out_files': {'out/report-20250115.txt': 'host: mx\nkernel: 5.15\nusers: 0\n'}}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_17(case):
    p01.check(V, case)

"""Автоматична перевірка варіанта 09."""
import pytest
from conftest import load
from kits import p01

V = load(9)
CASES = [{'id': '75% нижче порога 80',
  'public': True,
  'kind': 'script',
  'args': ['meminfo', '80'],
  'files': {'meminfo': 'MemTotal:       16000000 kB\n'
                       'MemFree:            1000 kB\n'
                       'MemAvailable:    4000000 kB\n'
                       'SwapTotal:       9999 kB\n'},
  'stdout': 'Memory: 75%\n',
  'code': 0},
 {'id': '75% вище порога 70',
  'public': True,
  'kind': 'script',
  'args': ['meminfo', '70'],
  'files': {'meminfo': 'MemTotal:       16000000 kB\n'
                       'MemFree:            1000 kB\n'
                       'MemAvailable:    4000000 kB\n'
                       'SwapTotal:       9999 kB\n'},
  'stdout': 'Memory: 75%\n',
  'code': 2,
  'stderr_contains': "Попередження: використання пам'яті досягло порогу"}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_09(case):
    p01.check(V, case)

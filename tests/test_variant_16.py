"""Автоматична перевірка варіанта 16."""
import pytest
from conftest import load
from kits import p01

V = load(16)
CASES = [{'id': 'навантаження в нормі',
  'public': True,
  'kind': 'script',
  'args': ['load.txt', '2.5'],
  'files': {'load.txt': '1.15 1.05 0.90 1/400 1234\n'},
  'stdout': 'LOAD OK 1.15\n',
  'code': 0},
 {'id': 'навантаження високе',
  'public': True,
  'kind': 'script',
  'args': ['load.txt', '1.0'],
  'files': {'load.txt': '1.15 1.05 0.90 1/400 1234\n'},
  'stdout': 'LOAD HIGH 1.15\n',
  'code': 1}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_16(case):
    p01.check(V, case)

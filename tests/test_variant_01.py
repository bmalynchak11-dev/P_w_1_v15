"""Автоматична перевірка варіанта 01."""
import pytest
from conftest import load
from kits import p01

V = load(1)
CASES = [{'id': 'підрахунок за спаданням',
  'public': True,
  'kind': 'script',
  'args': ['app.log'],
  'files': {'app.log': 'INFO: старт\n'
                       'ERROR: диск\n'
                       'INFO: запит\n'
                       'WARN: повільно\n'
                       'INFO: запит\n'
                       'ERROR: збій\n'
                       'DEBUG: деталі\n'},
  'stdout': 'INFO 3\nERROR 2\nDEBUG 1\nWARN 1\n',
  'code': 0},
 {'id': 'невідомі рівні ігноруються',
  'public': True,
  'kind': 'script',
  'args': ['app.log'],
  'files': {'app.log': 'TRACE: a\nerror: b\nINFO: c\nFATAL: d\n'},
  'stdout': 'INFO 1\n',
  'code': 0}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_01(case):
    p01.check(V, case)

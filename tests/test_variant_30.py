"""Автоматична перевірка варіанта 30."""
import pytest
from conftest import load
from kits import p01

V = load(30)
CASES = [{'id': 'перше збереження',
  'public': True,
  'kind': 'script',
  'args': ['src', 'store'],
  'files': {'src/app.conf': 'port=80\n', 'store/': ''},
  'stdout': 'SAVED app.conf\n',
  'code': 0},
 {'id': 'незмінений і змінений файли',
  'public': True,
  'kind': 'script',
  'args': ['src', 'store'],
  'files': {'src/a.conf': 'A=1\n',
            'src/b.conf': 'B=2\n',
            'store/a.conf.20250101-0200': 'A=1\n',
            'store/b.conf.20250101-0200': 'B=1\n'},
  'stdout': 'UNCHANGED a.conf\nSAVED b.conf\n',
  'code': 0}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_30(case):
    p01.check(V, case)

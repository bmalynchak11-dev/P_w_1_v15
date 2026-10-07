"""Автоматична перевірка варіанта 24."""
import pytest
from conftest import load
from kits import p01

V = load(24)
CASES = [{'id': 'два найбільші',
  'public': True,
  'kind': 'script',
  'args': ['data', '2'],
  'files': {'data/a.txt': 'abc', 'data/b.txt': 'bbbbbbbbbb', 'data/c.txt': 'ccccccc'},
  'stdout': '10 b.txt\n7 c.txt\n',
  'code': 0},
 {'id': 'рівні розміри за іменем',
  'public': True,
  'kind': 'script',
  'args': ['data', '3'],
  'files': {'data/x.log': 'xxxxx', 'data/m.log': 'mmmmm', 'data/k.log': 'k', 'data/z.log': 'zzzzzzzzz'},
  'stdout': '9 z.log\n5 m.log\n5 x.log\n',
  'code': 0}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_24(case):
    p01.check(V, case)

"""Автоматична перевірка варіанта 02."""
import pytest
from conftest import load
from kits import p01

V = load(2)
CASES = [{'id': 'перша копія',
  'public': True,
  'kind': 'script',
  'args': ['data', 'bak', '3'],
  'files': {'data/a.txt': 'A', 'bak/': ''},
  'stdout': 'СТВОРЕНО data-20250115.tar.gz\nЗалишено копій: 1\n',
  'code': 0,
  'listing': {'bak': ['data-20250115.tar.gz'], 'data': ['a.txt']}},
 {'id': 'видаляє найстарішу',
  'public': True,
  'kind': 'script',
  'args': ['data', 'bak', '3'],
  'files': {'data/a.txt': 'A',
            'bak/data-20250110.tar.gz': 'x',
            'bak/data-20250112.tar.gz': 'x',
            'bak/data-20250113.tar.gz': 'x'},
  'stdout': 'СТВОРЕНО data-20250115.tar.gz\nВИДАЛЕНО data-20250110.tar.gz\nЗалишено копій: 3\n',
  'code': 0,
  'listing': {'bak': ['data-20250112.tar.gz', 'data-20250113.tar.gz', 'data-20250115.tar.gz']}}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_02(case):
    p01.check(V, case)

"""Автоматична перевірка варіанта 06."""
import pytest
from conftest import load
from kits import p01

V = load(6)
CASES = [{'id': 'видаляє старі, keep_ лишає',
  'public': True,
  'kind': 'script',
  'args': ['tmp', '7'],
  'files': {'tmp/a.tmp': {'text': 'A', 'age_days': 10},
            'tmp/b.tmp': {'text': 'B', 'age_days': 2},
            'tmp/d.tmp': {'text': 'D', 'age_days': 20},
            'tmp/keep_c.tmp': {'text': 'C', 'age_days': 30}},
  'stdout': 'DELETE a.tmp\nDELETE d.tmp\nKEEP keep_c.tmp\nВидалено: 2\nЗахищено: 1\n',
  'code': 0,
  'listing': {'tmp': ['b.tmp', 'keep_c.tmp']}},
 {'id': 'dry-run нічого не змінює',
  'public': True,
  'kind': 'script',
  'args': ['tmp', '7', '--dry-run'],
  'files': {'tmp/a.tmp': {'text': 'A', 'age_days': 10}, 'tmp/b.tmp': {'text': 'B', 'age_days': 2}},
  'stdout': 'WOULD DELETE a.tmp\nБуло б видалено: 1\nЗахищено: 0\n',
  'code': 0,
  'listing': {'tmp': ['a.tmp', 'b.tmp']}}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_06(case):
    p01.check(V, case)

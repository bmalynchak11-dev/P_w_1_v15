"""Автоматична перевірка варіанта 25."""
import pytest
from conftest import load
from kits import p01

V = load(25)
CASES = [{'id': 'підсумки за відділами',
  'public': True,
  'kind': 'script',
  'args': ['data.csv'],
  'files': {'data.csv': 'відділ,сума\nСклад,100\nМаркетинг,250\nСклад,50\nКадри,75\n'},
  'stdout': 'Кадри: 75\nМаркетинг: 250\nСклад: 150\nРазом: 475\n',
  'code': 0},
 {'id': 'некоректний рядок у stderr',
  'public': True,
  'kind': 'script',
  'args': ['data.csv'],
  'files': {'data.csv': 'відділ,сума\nОхорона,40\nОхорона,abc\nЮристи,60\n'},
  'stdout': 'Охорона: 40\nЮристи: 60\nРазом: 100\n',
  'code': 0,
  'stderr_contains': 'Пропущено рядок 3: Охорона,abc'}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_25(case):
    p01.check(V, case)

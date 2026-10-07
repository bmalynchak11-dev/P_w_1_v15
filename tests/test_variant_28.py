"""Автоматична перевірка варіанта 28."""
import pytest
from conftest import load
from kits import p01

V = load(28)
CASES = [{'id': 'перший запуск без стану',
  'public': True,
  'kind': 'script',
  'args': ['app.log', 'state.txt'],
  'files': {'app.log': 'l1\nl2\nl3\nl4\nl5\n'},
  'stdout': 'Нових рядків: 5\n',
  'code': 0,
  'out_files': {'state.txt': '5\n'}},
 {'id': 'приріст на три рядки',
  'public': True,
  'kind': 'script',
  'args': ['app.log', 'state.txt'],
  'files': {'app.log': 'l1\nl2\nl3\nl4\nl5\nl6\nl7\nl8\n', 'state.txt': '5\n'},
  'stdout': 'Нових рядків: 3\n',
  'code': 0,
  'out_files': {'state.txt': '8\n'}}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_28(case):
    p01.check(V, case)

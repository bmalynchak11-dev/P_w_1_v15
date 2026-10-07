"""Автоматична перевірка варіанта 08."""
import pytest
from conftest import load
from kits import p01

V = load(8)
CASES = [{'id': 'знаходить файли з правом запису для всіх',
  'public': True,
  'kind': 'script',
  'args': ['share'],
  'files': {'share/a.txt': {'text': 'A', 'mode': 420},
            'share/b.txt': {'text': 'B', 'mode': 438},
            'share/docs/c.txt': {'text': 'C', 'mode': 511},
            'share/docs/d.txt': {'text': 'D', 'mode': 416}},
  'stdout': 'b.txt\ndocs/c.txt\nЗнайдено: 2\n',
  'code': 0,
  'modes': {'share/a.txt': 420, 'share/b.txt': 438, 'share/docs/c.txt': 511, 'share/docs/d.txt': 416}},
 {'id': 'таких файлів немає',
  'public': True,
  'kind': 'script',
  'args': ['share'],
  'files': {'share/a.txt': {'text': 'A', 'mode': 384}},
  'stdout': 'Знайдено: 0\n',
  'code': 0}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_08(case):
    p01.check(V, case)

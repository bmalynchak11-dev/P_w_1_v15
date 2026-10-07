"""Автоматична перевірка варіанта 12."""
import pytest
from conftest import load
from kits import p01

V = load(12)
CASES = [{'id': 'усі файли цілі',
  'public': True,
  'kind': 'script',
  'args': ['list.txt'],
  'files': {'a.txt': 'abc',
            'hello.txt': 'hello',
            'list.txt': 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad  a.txt\n'
                        '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824  hello.txt\n'},
  'stdout': 'OK a.txt\nOK hello.txt\nПеревірено: 2, пошкоджено: 0\n',
  'code': 0},
 {'id': 'один пошкоджений',
  'public': True,
  'kind': 'script',
  'args': ['list.txt'],
  'files': {'a.txt': 'abc',
            'b.txt': 'hello',
            'list.txt': 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad  a.txt\n'
                        'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  b.txt\n'},
  'stdout': 'OK a.txt\nFAILED b.txt\nПеревірено: 2, пошкоджено: 1\n',
  'code': 1}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_12(case):
    p01.check(V, case)

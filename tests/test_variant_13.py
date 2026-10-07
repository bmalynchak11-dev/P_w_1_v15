"""Автоматична перевірка варіанта 13."""
import pytest
from conftest import load
from kits import p01

V = load(13)
CASES = [{'id': 'створює двох користувачів',
  'public': True,
  'kind': 'script',
  'args': ['users.csv'],
  'files': {'users.csv': 'alice,dev,/bin/bash\nbob,ops,/bin/sh\n'},
  'shims': {'useradd': '@ok'},
  'stdout': 'Створено: 2\n',
  'code': 0,
  'shim_calls': {'useradd': ['-m -s /bin/bash -g dev alice', '-m -s /bin/sh -g ops bob']}},
 {'id': 'некоректний рядок пропущено',
  'public': True,
  'kind': 'script',
  'args': ['users.csv'],
  'files': {'users.csv': 'carol,dev,/bin/bash\nDave,dev,/bin/bash\neve,ops,/bin/zsh\n'},
  'shims': {'useradd': '@ok'},
  'stdout': 'Створено: 2\n',
  'code': 0,
  'stderr_contains': 'Пропущено рядок 2: некоректний формат',
  'shim_calls': {'useradd': ['-m -s /bin/bash -g dev carol', '-m -s /bin/zsh -g ops eve']}}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_13(case):
    p01.check(V, case)

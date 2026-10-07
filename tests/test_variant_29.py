"""Автоматична перевірка варіанта 29."""
import pytest
from conftest import load
from kits import p01

V = load(29)
CASES = [{'id': "топ-3 із п'яти користувачів",
  'public': True,
  'kind': 'script',
  'args': [],
  'shims': {'ps': 'printf "%s\\n" root alice nginx root root bob nginx alice root nginx mysql'},
  'stdout': 'root 4\nnginx 3\nalice 2\n',
  'code': 0},
 {'id': 'рівні кількості за алфавітом',
  'public': True,
  'kind': 'script',
  'args': [],
  'shims': {'ps': 'printf "%s\\n" carol alice dave bob alice carol dave bob root'},
  'stdout': 'alice 2\nbob 2\ncarol 2\n',
  'code': 0}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_29(case):
    p01.check(V, case)

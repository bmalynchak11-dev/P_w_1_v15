"""Автоматична перевірка варіанта 20."""
import pytest
from conftest import load
from kits import p01

V = load(20)
CASES = [{'id': 'успіх на другій спробі',
  'public': True,
  'kind': 'script',
  'args': ['3'],
  'shims': {'pg_isready': 'c=$(cat $HOME/c 2>/dev/null || echo 0); c=$((c+1)); echo $c > $HOME/c; [ $c -eq 2 '
                          ']'},
  'stdout': 'спроба 1: FAIL\nспроба 2: OK\n',
  'code': 0},
 {'id': 'повний фейл',
  'public': True,
  'kind': 'script',
  'args': ['2'],
  'shims': {'pg_isready': 'exit 1'},
  'stdout': 'спроба 1: FAIL\nспроба 2: FAIL\n',
  'code': 1}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_20(case):
    p01.check(V, case)

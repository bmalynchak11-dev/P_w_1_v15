"""Автоматична перевірка варіанта 27."""
import pytest
from conftest import load
from kits import p01

V = load(27)
CASES = [{'id': 'годинник синхронізовано',
  'public': True,
  'kind': 'script',
  'args': [],
  'shims': {'timedatectl': 'printf "%s\\n" "Time zone: Europe/Kyiv (EET, +0200)" "System clock synchronized: '
                           'yes" "NTP service: active"'},
  'stdout': 'SYNC OK\n',
  'code': 0},
 {'id': 'годинник не синхронізовано',
  'public': True,
  'kind': 'script',
  'args': [],
  'shims': {'timedatectl': 'printf "%s\\n" "System clock synchronized: no" "NTP service: inactive"'},
  'stdout': 'SYNC FAIL\n',
  'code': 1}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_27(case):
    p01.check(V, case)

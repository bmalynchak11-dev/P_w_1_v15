"""Автоматична перевірка варіанта 22."""
import pytest
from conftest import load
from kits import p01

V = load(22)
CASES = [{'id': 'неочікувані порти',
  'public': True,
  'kind': 'script',
  'args': ['allowed.txt'],
  'files': {'allowed.txt': '22\n80\n'},
  'shims': {'ss': "printf '%s\\n' 'State Recv-Q Send-Q Local Address:Port Peer Address:Port' 'LISTEN 0 128 "
                  "0.0.0.0:22 0.0.0.0:*' 'LISTEN 0 128 [::]:22 [::]:*' 'LISTEN 0 511 0.0.0.0:8080 0.0.0.0:*' "
                  "'LISTEN 0 128 127.0.0.1:631 0.0.0.0:*' 'LISTEN 0 511 *:80 *:*'"},
  'stdout': 'UNEXPECTED 631\nUNEXPECTED 8080\nПеревірено портів: 4\n',
  'code': 1,
  'shim_calls': {'ss': ['-tln']}},
 {'id': 'усі порти дозволені',
  'public': True,
  'kind': 'script',
  'args': ['allowed.txt'],
  'files': {'allowed.txt': '22\n631\n'},
  'shims': {'ss': "printf '%s\\n' 'State Recv-Q Send-Q Local Address:Port Peer Address:Port' 'LISTEN 0 128 "
                  "0.0.0.0:22 0.0.0.0:*' 'LISTEN 0 128 [::]:22 [::]:*' 'LISTEN 0 5 127.0.0.1:631 0.0.0.0:*'"},
  'stdout': 'Перевірено портів: 2\n',
  'code': 0}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_22(case):
    p01.check(V, case)

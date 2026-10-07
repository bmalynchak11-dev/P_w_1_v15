"""Автоматична перевірка варіанта 10."""
import pytest
from conftest import load
from kits import p01

V = load(10)
CASES = [{'id': "п'ять рядків різних класів",
  'public': True,
  'kind': 'script',
  'args': ['access.log'],
  'files': {'access.log': '10.0.0.1 - - [10/Oct:13:55:36 +0000] "GET / HTTP/1.1" 200 5 "-" "x"\n'
                          '10.0.0.1 - - [10/Oct:13:55:36 +0000] "GET / HTTP/1.1" 200 5 "-" "x"\n'
                          '10.0.0.1 - - [10/Oct:13:55:36 +0000] "GET / HTTP/1.1" 301 5 "-" "x"\n'
                          '10.0.0.1 - - [10/Oct:13:55:36 +0000] "GET / HTTP/1.1" 404 5 "-" "x"\n'
                          '10.0.0.1 - - [10/Oct:13:55:36 +0000] "GET / HTTP/1.1" 500 5 "-" "x"\n'},
  'stdout': '2xx: 2\n3xx: 1\n4xx: 1\n5xx: 1\n',
  'code': 0},
 {'id': 'шість рядків, багато 404',
  'public': True,
  'kind': 'script',
  'args': ['access.log'],
  'files': {'access.log': '10.0.0.1 - - [10/Oct:13:55:36 +0000] "GET / HTTP/1.1" 200 5 "-" "x"\n'
                          '10.0.0.1 - - [10/Oct:13:55:36 +0000] "GET / HTTP/1.1" 304 5 "-" "x"\n'
                          '10.0.0.1 - - [10/Oct:13:55:36 +0000] "GET / HTTP/1.1" 404 5 "-" "x"\n'
                          '10.0.0.1 - - [10/Oct:13:55:36 +0000] "GET / HTTP/1.1" 404 5 "-" "x"\n'
                          '10.0.0.1 - - [10/Oct:13:55:36 +0000] "GET / HTTP/1.1" 404 5 "-" "x"\n'
                          '10.0.0.1 - - [10/Oct:13:55:36 +0000] "GET / HTTP/1.1" 502 5 "-" "x"\n'},
  'stdout': '2xx: 1\n3xx: 1\n4xx: 3\n5xx: 1\n',
  'code': 0}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_10(case):
    p01.check(V, case)

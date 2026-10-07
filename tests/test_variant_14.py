"""Автоматична перевірка варіанта 14."""
import pytest
from conftest import load
from kits import p01

V = load(14)
CASES = [{'id': 'усі адреси доступні',
  'public': True,
  'kind': 'script',
  'args': ['http://site-a.test', 'http://site-c.test'],
  'shims': {'curl': 'case "$*" in *site-a*) printf 200;; *site-b*) printf 404;; *site-c*) printf 301;; '
                    '*site-d*) printf 503;; *edge199*) printf 199;; *edge200*) printf 200;; *edge299*) '
                    'printf 299;; *edge300*) printf 300;; *edge399*) printf 399;; *edge400*) printf 400;; *) '
                    'printf 000;; esac'},
  'stdout': 'http://site-a.test 200\nhttp://site-c.test 301\n',
  'code': 0,
  'shim_calls': {'curl': ['-s -o /dev/null -w %{http_code} http://site-a.test',
                          '-s -o /dev/null -w %{http_code} http://site-c.test']}},
 {'id': 'є недоступні адреси',
  'public': True,
  'kind': 'script',
  'args': ['http://site-a.test', 'http://site-b.test', 'http://site-d.test'],
  'shims': {'curl': 'case "$*" in *site-a*) printf 200;; *site-b*) printf 404;; *site-c*) printf 301;; '
                    '*site-d*) printf 503;; *edge199*) printf 199;; *edge200*) printf 200;; *edge299*) '
                    'printf 299;; *edge300*) printf 300;; *edge399*) printf 399;; *edge400*) printf 400;; *) '
                    'printf 000;; esac'},
  'stdout': 'http://site-a.test 200\nhttp://site-b.test 404\nhttp://site-d.test 503\n',
  'code': 2}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_14(case):
    p01.check(V, case)

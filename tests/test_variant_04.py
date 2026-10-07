"""Автоматична перевірка варіанта 04."""
import pytest
from conftest import load
from kits import p01

V = load(4)
CASES = [{'id': 'звичайні користувачі з оболонкою',
  'public': True,
  'kind': 'script',
  'args': ['passwd'],
  'files': {'passwd': 'root:x:0:0:root:/root:/bin/bash\n'
                      'daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n'
                      'alice:x:1001:1001:Alice:/home/alice:/bin/bash\n'
                      'bob:x:1000:1000:Bob:/home/bob:/bin/zsh\n'
                      'svc:x:1002:1002::/home/svc:/usr/sbin/nologin\n'
                      'temp:x:1003:1003::/home/temp:/bin/false\n'
                      'nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin\n'},
  'stdout': 'bob\nalice\n',
  'code': 0},
 {'id': 'лише системні облікові записи',
  'public': True,
  'kind': 'script',
  'args': ['passwd'],
  'files': {'passwd': 'root:x:0:0:root:/root:/bin/bash\n'
                      'daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n'
                      'www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\n'},
  'stdout': 'Немає\n',
  'code': 0}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_04(case):
    p01.check(V, case)

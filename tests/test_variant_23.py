"""Автоматична перевірка варіанта 23."""
import pytest
from conftest import load
from kits import p01

V = load(23)
CASES = [{'id': 'додано, видалено, змінено',
  'public': True,
  'kind': 'script',
  'args': ['inv'],
  'files': {'inv/packages-20250114.txt': 'bash 5.2.15-2\ncurl 7.88.1-10\nnano 7.2-1\nopenssl 3.0.11-1\n'},
  'shims': {'dpkg-query': "printf '%s\\n' 'openssl 3.0.13-1' 'bash 5.2.15-2' 'git 1:2.39.2-1' 'curl "
                          "7.88.1-10'"},
  'stdout': 'ADDED git\nREMOVED nano\nCHANGED openssl\nЗмін: 3\n',
  'code': 0,
  'out_files': {'inv/packages-20250115.txt': 'bash 5.2.15-2\n'
                                             'curl 7.88.1-10\n'
                                             'git 1:2.39.2-1\n'
                                             'openssl 3.0.13-1\n'}},
 {'id': 'перший запуск',
  'public': True,
  'kind': 'script',
  'args': ['inv'],
  'files': {'inv/': ''},
  'shims': {'dpkg-query': "printf '%s\\n' 'zsh 5.9-4' 'bash 5.2.15-2'"},
  'stdout': 'Перший запуск: збережено пакетів: 2\n',
  'code': 0,
  'out_files': {'inv/packages-20250115.txt': 'bash 5.2.15-2\nzsh 5.9-4\n'}}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_23(case):
    p01.check(V, case)

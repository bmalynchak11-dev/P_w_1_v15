"""Автоматична перевірка варіанта 03."""
import pytest
from conftest import load
from kits import p01

V = load(3)
CASES = [{'id': 'попередження за порогом',
  'public': True,
  'kind': 'script',
  'args': ['80'],
  'shims': {'df': "printf '%s\\n' 'Файлова система Розмір Зайнято Доступно Викор% Змонтовано' '/dev/sda1 20G "
                  "9G 11G 45% /' '/dev/sda2 1G 800M 200M 80% /boot' '/dev/sdb1 100G 92G 8G 92% /var' "
                  "'/dev/sdc1 200G 158G 42G 79% /home'"},
  'stdout': 'WARN /boot 80%\nWARN /var 92%\n',
  'code': 1},
 {'id': 'усе гаразд',
  'public': True,
  'kind': 'script',
  'args': ['90'],
  'shims': {'df': "printf '%s\\n' 'Файлова система Розмір Зайнято Доступно Викор% Змонтовано' '/dev/sda1 20G "
                  "9G 11G 45% /' '/dev/sdb1 100G 60G 40G 60% /data'"},
  'stdout': 'OK\n',
  'code': 0}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_03(case):
    p01.check(V, case)

"""Автоматична перевірка варіанта 05."""
import pytest
from conftest import load
from kits import p01

V = load(5)
CASES = [{'id': 'IP за порогом',
  'public': True,
  'kind': 'script',
  'args': ['auth.log', '3'],
  'files': {'auth.log': 'Jan 15 10:00:01 srv sshd[812]: Failed password for root from 10.0.0.5 port 4022\n'
                        'Jan 15 10:00:05 srv sshd[813]: Failed password for admin from 192.168.1.20 port '
                        '4100\n'
                        'Jan 15 10:00:09 srv sshd[814]: Failed password for invalid user test from 10.0.0.5 '
                        'port 4030\n'
                        'Jan 15 10:00:12 srv sshd[815]: Accepted password for alice from 10.0.0.7 port 5000\n'
                        'Jan 15 10:00:15 srv sshd[816]: Failed password for root from 10.0.0.7 port 4200\n'
                        'Jan 15 10:00:20 srv sshd[817]: Failed password for root from 10.0.0.5 port 4044\n'
                        'Jan 15 10:00:25 srv sshd[818]: Failed password for admin from 192.168.1.20 port '
                        '4101\n'
                        'Jan 15 10:00:30 srv sshd[819]: Invalid user guest from 10.0.0.7 port 4300\n'
                        'Jan 15 10:00:35 srv sshd[820]: Failed password for root from 10.0.0.5 port 4055\n'
                        'Jan 15 10:00:40 srv sshd[821]: Failed password for admin from 192.168.1.20 port '
                        '4102\n'
                        'Jan 15 10:00:45 srv sshd[822]: Failed password for root from 10.0.0.7 port 4201\n'},
  'stdout': '10.0.0.5 4\n192.168.1.20 3\n',
  'code': 0},
 {'id': 'жоден IP не досяг порогу',
  'public': True,
  'kind': 'script',
  'args': ['auth.log', '5'],
  'files': {'auth.log': 'Jan 15 11:00:01 srv sshd[900]: Failed password for root from 10.0.0.9 port 3000\n'
                        'Jan 15 11:00:02 srv sshd[901]: Failed password for root from 10.0.0.9 port 3001\n'
                        'Jan 15 11:00:03 srv sshd[902]: Failed password for bob from 172.16.0.4 port 3002\n'},
  'stdout': 'Підозрілих IP немає\n',
  'code': 0}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_05(case):
    p01.check(V, case)

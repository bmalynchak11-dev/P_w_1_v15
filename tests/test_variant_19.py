"""Автоматична перевірка варіанта 19."""
import pytest
from conftest import load
from kits import p01

V = load(19)
CASES = [{'id': 'виправляє лише потрібне',
  'public': True,
  'kind': 'script',
  'args': ['cfg'],
  'files': {'cfg/a.conf': {'text': '', 'mode': 420},
            'cfg/b.sh': {'text': '', 'mode': 488},
            'cfg/c.txt': {'text': '', 'mode': 384}},
  'stdout': 'FIXED cfg/a.conf 644→640\nВиправлено: 1\n',
  'code': 0,
  'modes': {'cfg/a.conf': 416, 'cfg/b.sh': 488, 'cfg/c.txt': 384}},
 {'id': 'нічого виправляти',
  'public': True,
  'kind': 'script',
  'args': ['cfg'],
  'files': {'cfg/a.conf': {'text': '', 'mode': 416}},
  'stdout': 'Виправлено: 0\n',
  'code': 0,
  'modes': {'cfg/a.conf': 416}}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_19(case):
    p01.check(V, case)

"""Автоматична перевірка варіанта 18."""
import pytest
from conftest import load
from kits import p01

V = load(18)
CASES = [{'id': 'видаляє зайві файли',
  'public': True,
  'kind': 'script',
  'args': ['backups', '*.gz', '2'],
  'files': {'backups/a.gz': '', 'backups/b.gz': '', 'backups/c.gz': '', 'backups/d.gz': ''},
  'stdout': 'DELETED a.gz\nDELETED b.gz\n',
  'code': 0,
  'listing': {'backups': ['c.gz', 'd.gz']}},
 {'id': 'файлів менше ніж N',
  'public': True,
  'kind': 'script',
  'args': ['backups', '*.gz', '5'],
  'files': {'backups/x.gz': '', 'backups/y.gz': ''},
  'stdout': '',
  'code': 0,
  'listing': {'backups': ['x.gz', 'y.gz']}}]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_variant_18(case):
    p01.check(V, case)

"""Службовий файл варіанта 26. Не змінюйте його: ви редагуєте файли в папці variant_26/."""
from pathlib import Path

DIR = Path(__file__).resolve().parent / "variant_26"
FILES = ['task.service', 'task.sh', 'task.timer']
for _name in FILES:
    if "TODO: реалізуйте" in (DIR / _name).read_text(encoding="utf-8"):
        raise NotImplementedError(f"Файл {_name} (варіанта 26) ще не реалізовано: виконайте завдання за карткою і приберіть позначку TODO")

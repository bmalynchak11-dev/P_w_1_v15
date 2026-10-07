"""Службовий файл варіанта 19. Не змінюйте його: ви редагуєте файли в папці variant_19/."""
from pathlib import Path

DIR = Path(__file__).resolve().parent / "variant_19"
FILES = ['task.service', 'task.sh', 'task.timer']
for _name in FILES:
    if "TODO: реалізуйте" in (DIR / _name).read_text(encoding="utf-8"):
        raise NotImplementedError(f"Файл {_name} (варіанта 19) ще не реалізовано: виконайте завдання за карткою і приберіть позначку TODO")

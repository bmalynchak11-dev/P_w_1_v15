"""Допоміжний завантажувач: підключає службовий файл варіанта з папки variants/ (або з VARIANT_DIR)."""
import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def load(number):
    """Повертає службовий модуль варіанта з номером number (атрибут DIR — папка з вашими файлами)."""
    base = Path(os.environ.get("VARIANT_DIR", ROOT.parent / "variants"))
    path = base / f"variant_{number:02d}.py"
    if not path.exists():
        raise FileNotFoundError(f"Не знайдено файл варіанта {number:02d} у {base}")
    spec = importlib.util.spec_from_file_location(f"variant_{number:02d}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

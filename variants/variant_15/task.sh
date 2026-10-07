#!/usr/bin/env bash

# Правило 1: рівно 2 аргументи
if [ "$#" -ne 2 ]; then
    echo "Використання: task.sh ДЖЕРЕЛО ПРИЗНАЧЕННЯ" >&2
    exit 2
fi

SRC="$1"
DEST="$2"

# Правило 2: ДЖЕРЕЛО має бути каталогом
if [ ! -d "$SRC" ]; then
    echo "Помилка: джерело не є каталогом" >&2
    exit 3
fi

# Правило 3: ДЖЕРЕЛО і ПРИЗНАЧЕННЯ не повинні збігатися як рядки
if [ "$SRC" = "$DEST" ]; then
    echo "Помилка: джерело і призначення збігаються" >&2
    exit 4
fi

# Правило 4: перевірка, чи не порожній каталог ДЖЕРЕЛО (включно з прихованими файлами)
if [ -z "$(ls -A "$SRC")" ]; then
    echo "Помилка: джерело порожнє" >&2
    exit 5
fi

# Формування мітки часу (РРРР-ММ-ДД ГГ:ХХ)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
LOG_FILE="${DEST}.log"

# Правило 5 та 7: виконання rsync
if rsync -a --delete "${SRC}/" "${DEST}/"; then
    echo "${TIMESTAMP} OK" >> "$LOG_FILE"
    exit 0
else
    echo "${TIMESTAMP} FAIL" >> "$LOG_FILE"
    echo "Помилка: rsync завершився невдало" >&2
    exit 1
fi
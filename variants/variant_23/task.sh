#!/usr/bin/env bash
# Інвентар пакетів: task.sh КАТАЛОГ
# Підказки: dpkg-query -W -f='${Package} ${Version}\n'; date +%Y%m%d; sort; find -name 'packages-*.txt';
#           diff старий новий (рядки '< ' і '> '); cut -c3-; cut -d' ' -f1; grep -qxF
# TODO: реалізуйте скрипт за карткою варіанта

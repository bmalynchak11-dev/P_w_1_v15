#!/usr/bin/env bash
# Найбільші файли каталогу: task.sh КАТАЛОГ N
# Підказки: find "$dir" -maxdepth 1 -type f; stat -c %s файл; basename;
#           sort -k1,1nr -k2; head -n "$n"; case для перевірки, що N — лише цифри
# TODO: реалізуйте скрипт за карткою варіанта

#!/usr/bin/env bash
# Зведення журналу journald за службами: task.sh (без аргументів)
# Підказки: journalctl -o short --no-pager; awk '{print $5}'; cut -d'[' -f1; cut -d: -f1;
#           sort | uniq -c; sort -k1,1nr; head -n 3
# TODO: реалізуйте скрипт за карткою варіанта

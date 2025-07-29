#!/bin/bash
# Запускает SMITH Cockpit с новой, динамической задачей.

# Сначала удалим старый отчет, если он есть, для чистоты эксперимента
rm -f /data/data/com.termux/files/home/report.txt

python /data/data/com.termux/files/home/SMITH_FRAMEWORK/interactive_cockpit.py --prompt "Создай файл report.txt, напиши в него 'Отчет готов' и покажи мне результат." --project-root "/data/data/com.termux/files/home"
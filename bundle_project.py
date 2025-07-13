#!/usr/bin/env python3
import os
import sys
import fnmatch

# Путь к корню проекта (скрипт должен лежать в корне)
ROOT = os.path.abspath(os.path.dirname(__file__))

# Шаблоны файлов для исключения из сборки кода
EXCLUDE_PATTERNS = ['*.log', '*.lock']

# Функция для печати дерева файлов
def print_tree(path, prefix=""):
    entries = sorted(os.listdir(path))
    for i, name in enumerate(entries):
        full = os.path.join(path, name)
        is_last = (i == len(entries) - 1)
        pointer = '└── ' if is_last else '├── '
        print(prefix + pointer + name)
        if os.path.isdir(full):
            extension = '    ' if is_last else '│   '
            print_tree(full, prefix + extension)

# Проверка, нужно ли исключать файл по имени
def is_excluded(filename):
    return any(fnmatch.fnmatch(filename, pattern) for pattern in EXCLUDE_PATTERNS)


def main():
    # 1. Дерево
    print(f"Проект: {os.path.basename(ROOT)}")
    print_tree(ROOT)
    print("\n\n")

    # 2. Сборка кода
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # Относительный путь директории
        reldir = os.path.relpath(dirpath, ROOT)
        for fname in sorted(filenames):
            # Пропускаем скрытые файлы и сам скрипт
            if fname.startswith('.') or fname == os.path.basename(__file__):
                continue
            # Пропускаем по маскам исключения
            if is_excluded(fname):
                continue

            fullpath = os.path.join(dirpath, fname)
            relpath = os.path.normpath(os.path.join(reldir, fname))
            if relpath.startswith(os.pardir):
                relpath = fname  # на всякий случай

            # Печатаем тег-открытие
            print(f"<{relpath}>")
            try:
                with open(fullpath, 'r', encoding='utf-8') as f:
                    sys.stdout.write(f.read())
            except UnicodeDecodeError:
                # Если файл бинарный — просто пропустим
                print(f"# (не удалось прочитать {relpath} в текстовом виде)")
            # Тег-закрытие
            print(f"</{relpath}>")
            # Пустые строки между файлами
            print("\n")


if __name__ == "__main__":
    main()

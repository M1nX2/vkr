#!/usr/bin/env python
"""
Кастомный скрипт запуска Django, который обрабатывает ошибки подключения к БД
"""
import os
import sys

# Настройка Django перед импортом
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vkr_project.settings')

import django
django.setup()

from django.core.management import execute_from_command_line
from django.core.management.commands.runserver import Command as RunserverCommand
from django.db.utils import OperationalError, DatabaseError

# Монки-патчим метод check_migrations для обработки ошибок БД
original_check_migrations = RunserverCommand.check_migrations

def patched_check_migrations(self):
    """Переопределяем проверку миграций, чтобы не падать при недоступной БД"""
    try:
        return original_check_migrations(self)
    except (OperationalError, DatabaseError) as e:
        # Если БД недоступна, просто выводим предупреждение и продолжаем
        self.stdout.write(
            self.style.WARNING(
                f'\n⚠️  Warning: Database is unavailable ({str(e)[:100]}). '
                'Skipping migration checks. Django will continue to run, '
                'but database features may be limited.\n'
            )
        )
    except Exception as e:
        # Для других ошибок также выводим предупреждение
        self.stdout.write(
            self.style.WARNING(
                f'\n⚠️  Warning: Migration check failed ({str(e)[:100]}). Continuing anyway.\n'
            )
        )

# Монки-патчим метод check для обработки ошибок БД при проверке URL
original_check = RunserverCommand.check

def patched_check(self, *args, **kwargs):
    """Переопределяем проверку, чтобы не падать при недоступной БД"""
    try:
        return original_check(self, *args, **kwargs)
    except (OperationalError, DatabaseError) as e:
        # Если БД недоступна при проверке, просто выводим предупреждение и продолжаем
        self.stdout.write(
            self.style.WARNING(
                f'\n⚠️  Warning: Database is unavailable during checks ({str(e)[:100]}). '
                'Skipping database-related checks. Django will continue to run, '
                'but database features may be limited.\n'
            )
        )
    except Exception as e:
        # Для других ошибок также выводим предупреждение, но не прерываем запуск
        error_msg = str(e)
        # Игнорируем ошибки, связанные с БД при проверке URL
        if 'Can\'t connect' in error_msg or 'OperationalError' in error_msg or 'DatabaseError' in error_msg:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  Warning: Database-related error during checks ({error_msg[:100]}). '
                    'Continuing anyway.\n'
                )
            )
        else:
            # Для других ошибок просто выводим предупреждение
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  Warning: Check failed ({error_msg[:100]}). Continuing anyway.\n'
                )
            )

# Применяем патчи
RunserverCommand.check_migrations = patched_check_migrations
RunserverCommand.check = patched_check

if __name__ == '__main__':
    # Получаем порт из переменной окружения или используем значение по умолчанию
    port = os.environ.get('DJANGO_PORT', '3000')
    host = '0.0.0.0'
    
    # Запускаем сервер
    execute_from_command_line(['manage.py', 'runserver', f'{host}:{port}'])


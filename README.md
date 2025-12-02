# VKR Frontend (Django)

Django фронтенд для системы детекции нарушений у собак.

## Требования

- Docker и Docker Compose

## Быстрый старт

### Запуск фронтенда

```bash
docker-compose up -d
```

Фронтенд будет доступен на `http://localhost:3000`

### Настройка Django (при первом запуске)

Миграции выполняются автоматически при запуске контейнера.

Если нужно выполнить вручную:
```bash
docker-compose exec django-app python manage.py migrate
docker-compose exec django-app python manage.py createsuperuser
```

## Структура проекта

- `vkr_project/` - Основной проект Django
- `violations/` - Приложение для работы с нарушениями
- `templates/` - HTML шаблоны
- `docker/nginx/` - Конфигурация Nginx

## Переменные окружения

- `SECRET_KEY` - Секретный ключ Django (по умолчанию: django-insecure-change-this-in-production)
- `DEBUG` - Режим отладки (по умолчанию: True)
- `DB_HOST=mysql` - Хост базы данных
- `DB_DATABASE=laravel` - Имя базы данных
- `DB_USERNAME=root` - Пользователь БД
- `DB_PASSWORD=secret` - Пароль БД
- `PYTHON_API_URL=http://neurodog-backend:8000` - URL бэкенда

## Работа в общей сети

Проект использует сеть `app-network`, которая создается автоматически при запуске. Если бэкенд (NeuroDog-1) запущен в той же сети, они могут общаться друг с другом.

Nginx автоматически проксирует запросы к бэкенду через `/api/` на `http://neurodog-backend:8000/`

## API Endpoints

- `GET /` - Главная страница
- `POST /api/video/upload` - Загрузка видео
- `GET /api/violations` - Список нарушений
- `GET /api/violations/<video_id>` - Нарушения для видео
- `GET /api/video/progress/<video_id>` - Прогресс обработки
- `GET /api/video/<video_id>` - Получить обработанное видео
- `GET /report` - Страница отчетов
- `POST /report` - Формирование отчета
- `GET /report/export` - Экспорт в Excel

## Остановка

```bash
docker-compose down
```
## Volumes

- `mysql_data` - Данные MySQL
- `django-static` - Статические файлы Django
- `django-media` - Медиа файлы


# VKR Frontend (Django)

Django фронтенд для системы детекции нарушений у собак.

## Требования

- Docker и Docker Compose

## Быстрый старт

1. Скопируйте рабочий OpenVPN-конфиг (и связанные ключи/сертификаты) в `vkr/config`. По умолчанию используется файл `client.ovpn`.
2. Запустите Docker Compose:
   ```bash
   docker compose up -d --build
   ```
3. Фронтенд будет доступен на `http://localhost:3000`.

### Проверка

- Логи OpenVPN: `docker compose logs -f openvpn-client`
- Логи Django: `docker compose logs -f django-app`

### Администрирование Django

Миграции выполняются автоматически, но их можно повторить вручную:
```bash
docker compose exec django-app python manage.py migrate
docker compose exec django-app python manage.py createsuperuser
```

## Структура проекта

- `vkr_project/` – основной проект Django
- `violations/` – приложение для работы с нарушениями
- `templates/` – HTML-шаблоны
- `openvpn-client/` – минимальный образ OpenVPN-клиента
- `config/` – конфиги и ключи VPN (монтируются только в OpenVPN-контейнер)

## Переменные окружения

### Локальное окружение (по умолчанию)

Для работы с локальным бэкендом на том же хосте используйте:

```bash
export DB_HOST=host.docker.internal
export DB_PORT=3306
export PYTHON_API_URL=http://host.docker.internal:8000
docker compose up -d --build
```

Или создайте файл `.env` в корне проекта:

```bash
DB_HOST=host.docker.internal
DB_PORT=3306
DB_DATABASE=laravel
DB_USERNAME=root
DB_PASSWORD=secret
PYTHON_API_URL=http://host.docker.internal:8000
PYTHON_API_URL_FALLBACK=http://10.0.70.14:8000
```

### Удалённое окружение через VPN

Для работы с удалённым бэкендом через VPN:

```bash
export DB_HOST=10.0.70.2
export DB_PORT=3306
export PYTHON_API_URL=http://10.0.70.2:8000
export PYTHON_API_URL_FALLBACK=http://10.0.70.14:8000
docker compose up -d --build
```

Или в файле `.env`:

```bash
DB_HOST=10.0.70.2
DB_PORT=3306
DB_DATABASE=laravel
DB_USERNAME=root
DB_PASSWORD=secret
PYTHON_API_URL=http://10.0.70.2:8000
PYTHON_API_URL_FALLBACK=http://10.0.70.14:8000
```

### Все переменные окружения

- `SECRET_KEY` – секретный ключ Django (по умолчанию: `django-insecure-change-this-in-production`)
- `DEBUG` – режим отладки (`True` по умолчанию)
- `ALLOWED_HOSTS` – список хостов, которым разрешён доступ
- `CSRF_TRUSTED_ORIGINS` – доверенные источники для CSRF
- `DJANGO_PORT` – порт внутри контейнера (по умолчанию `3000`)
- `DB_HOST` – адрес MySQL (по умолчанию `host.docker.internal` для локального окружения)
- `DB_PORT` – порт MySQL (по умолчанию `3306`)
- `DB_DATABASE` – имя базы данных (по умолчанию `laravel`)
- `DB_USERNAME` – пользователь MySQL (по умолчанию `root`)
- `DB_PASSWORD` – пароль MySQL (по умолчанию `secret`)
- `PYTHON_API_URL` – основной адрес FastAPI-бэкенда (по умолчанию `http://host.docker.internal:8000`)
- `PYTHON_API_URL_FALLBACK` – резервный адрес FastAPI-бэкенда (по умолчанию `http://10.0.70.14:8000`)

Переменные OpenVPN:

- `OPENVPN_CONFIG` – путь к основному `.ovpn` (по умолчанию `/vpn/client.ovpn`)
- `OPENVPN_ARGS` – дополнительные аргументы при запуске клиента

Все файлы, указанные в конфигурации (`ca`, `cert`, `key`, `auth-user-pass` и т.д.), должны лежать в каталоге `config/`.

## Сеть

- Контейнер `openvpn-client` подключается к удалённому VPN и настраивает маршрутизацию для VPN-сетей.
- Контейнер `django-app` находится в сети `app-network` и имеет прямой доступ на порт `8081:3000`.
- При использовании VPN-адресов (10.0.70.x или 10.0.60.x) Django автоматически настраивает маршруты через `openvpn-client` для доступа к удалённым сервисам.
- При использовании локальных адресов (`host.docker.internal`) VPN-маршруты не настраиваются, и Django подключается напрямую к хосту.

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

- `django-static` – собранные статические файлы
- `django-media` – пользовательские загрузки


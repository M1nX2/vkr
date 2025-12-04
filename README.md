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

- `SECRET_KEY` – секретный ключ Django (по умолчанию: `django-insecure-change-this-in-production`)
- `DEBUG` – режим отладки (`True` по умолчанию)
- `ALLOWED_HOSTS` – список хостов, которым разрешён доступ
- `CSRF_TRUSTED_ORIGINS` – доверенные источники для CSRF
- `DJANGO_PORT` – порт внутри контейнера (по умолчанию `3000`, пробрасывается через OpenVPN-сервис)
- `DB_HOST`, `DB_PORT`, `DB_DATABASE`, `DB_USERNAME`, `DB_PASSWORD` – параметры MySQL (адрес должен быть доступен через VPN)
- `PYTHON_API_URL`, `PYTHON_API_URL_FALLBACK` – адреса FastAPI-бэкенда за VPN

Переменные OpenVPN:

- `OPENVPN_CONFIG` – путь к основному `.ovpn` (по умолчанию `/vpn/client.ovpn`)
- `OPENVPN_ARGS` – дополнительные аргументы при запуске клиента

Все файлы, указанные в конфигурации (`ca`, `cert`, `key`, `auth-user-pass` и т.д.), должны лежать в каталоге `config/`.

## Сеть

- Контейнер `openvpn-client` подключается к удалённому VPN и публикует порт `3000` на хост.
- Контейнер `django-app` использует сетевой namespace OpenVPN-клиента (`network_mode: "service:openvpn-client"`), поэтому весь исходящий трафик к бэкенду/БД идёт через VPN, а входящие запросы приходят через проброшенный порт.
- Docker создаёт сеть `app-network`, но порт наружу пробрасывается самим OpenVPN-клиентом.

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


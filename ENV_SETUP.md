# Настройка окружений

## Локальное окружение (для разработки)

Если у вас бэкенд запущен локально на порту 8000, используйте:

```bash
# Вариант 1: Через переменные окружения
export DB_HOST=host.docker.internal
export PYTHON_API_URL=http://host.docker.internal:8000
docker compose up -d --build

# Вариант 2: Через .env файл (создайте файл .env в корне vkr/)
DB_HOST=host.docker.internal
PYTHON_API_URL=http://host.docker.internal:8000
```

Затем запустите:
```bash
docker compose up -d --build
```

## Удалённое окружение через VPN

Если бэкенд находится на удалённом сервере через VPN:

```bash
# Вариант 1: Через переменные окружения
export DB_HOST=10.0.70.2
export PYTHON_API_URL=http://10.0.70.2:8000
export PYTHON_API_URL_FALLBACK=http://10.0.70.14:8000
docker compose up -d --build

# Вариант 2: Через .env файл
DB_HOST=10.0.70.2
PYTHON_API_URL=http://10.0.70.2:8000
PYTHON_API_URL_FALLBACK=http://10.0.70.14:8000
```

## Проверка подключения

После запуска проверьте логи:

```bash
# Логи Django
docker compose logs -f django-app

# Логи OpenVPN
docker compose logs -f openvpn-client
```

Django должен успешно подключиться к MySQL и запуститься на порту 3000 (доступен на хосте как 8081).


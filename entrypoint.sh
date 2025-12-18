#!/bin/sh
# Не прерываем выполнение при ошибках - Django должен запуститься даже если БД недоступна
set +e

DJANGO_PORT=${DJANGO_PORT:-3000}
VPN_GATEWAY=${VPN_GATEWAY:-openvpn-client}
# Используем переменные окружения из docker-compose напрямую (без значений по умолчанию)
# Значения по умолчанию задаются в docker-compose.yml
DB_HOST="${DB_HOST}"
PYTHON_API_URL="${PYTHON_API_URL}"

# Проверяем, нужно ли настраивать VPN маршруты
# Если DB_HOST или PYTHON_API_URL содержат VPN IP (10.0.70.x или 10.0.60.x), настраиваем маршруты
NEED_VPN_ROUTES=false

if [ -n "$DB_HOST" ] && echo "$DB_HOST" | grep -qE '^10\.0\.(70|60)\.'; then
  NEED_VPN_ROUTES=true
fi

if [ -n "$PYTHON_API_URL" ] && echo "$PYTHON_API_URL" | grep -qE '10\.0\.(70|60)\.'; then
  NEED_VPN_ROUTES=true
fi

if [ "$NEED_VPN_ROUTES" = "true" ]; then
  # Резолвим IP шлюза через DNS
  echo "Resolving VPN gateway IP for $VPN_GATEWAY..."
  VPN_GATEWAY_IP=$(getent hosts $VPN_GATEWAY 2>/dev/null | awk '{ print $1 }')

  if [ -z "$VPN_GATEWAY_IP" ]; then
    echo "Warning: Could not resolve $VPN_GATEWAY, skipping VPN routes"
  else
    # Добавляем маршруты для VPN-сетей через OpenVPN gateway
    echo "Configuring VPN routes through $VPN_GATEWAY ($VPN_GATEWAY_IP)..."
    ip route add 10.0.70.0/24 via $VPN_GATEWAY_IP 2>/dev/null || echo "Route 10.0.70.0/24 already exists"
    ip route add 10.0.60.0/24 via $VPN_GATEWAY_IP 2>/dev/null || echo "Route 10.0.60.0/24 already exists"
    
    echo "Current routes:"
    ip route
  fi
else
  echo "Local environment detected (DB_HOST=$DB_HOST), skipping VPN routes"
fi

# Проверяем доступность БД перед миграциями (не критично, если недоступна)
echo "Checking database availability..."
if [ -n "$DB_HOST" ]; then
  # Пытаемся применить миграции, но не прерываем выполнение при ошибке
  python manage.py migrate --noinput 2>&1 | head -5
  MIGRATE_EXIT_CODE=$?
  if [ $MIGRATE_EXIT_CODE -eq 0 ]; then
    echo "Migrations applied successfully"
  else
    echo "Warning: Migrations failed or database unavailable (exit code: $MIGRATE_EXIT_CODE)"
    echo "Django will continue to run, but database features may be limited"
  fi
else
  echo "DB_HOST not set, skipping migrations"
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Warning: Static files collection failed"

echo "Starting Django on port $DJANGO_PORT"
# Используем кастомный скрипт запуска, который обрабатывает ошибки БД
exec python run_django.py


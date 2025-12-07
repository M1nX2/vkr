#!/bin/sh
set -e

DJANGO_PORT=${DJANGO_PORT:-3000}
VPN_GATEWAY=${VPN_GATEWAY:-openvpn-client}
DB_HOST=${DB_HOST:-host.docker.internal}
PYTHON_API_URL=${PYTHON_API_URL:-http://host.docker.internal:8000}

# Проверяем, нужно ли настраивать VPN маршруты
# Если DB_HOST или PYTHON_API_URL содержат VPN IP (10.0.70.x или 10.0.60.x), настраиваем маршруты
NEED_VPN_ROUTES=false

if echo "$DB_HOST" | grep -qE '^10\.0\.(70|60)\.'; then
  NEED_VPN_ROUTES=true
fi

if echo "$PYTHON_API_URL" | grep -qE '10\.0\.(70|60)\.'; then
  NEED_VPN_ROUTES=true
fi

if [ "$NEED_VPN_ROUTES" = "true" ]; then
  # Резолвим IP шлюза через DNS
  echo "Resolving VPN gateway IP for $VPN_GATEWAY..."
  VPN_GATEWAY_IP=$(getent hosts $VPN_GATEWAY | awk '{ print $1 }')

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

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Django on port $DJANGO_PORT"
exec python manage.py runserver 0.0.0.0:"$DJANGO_PORT"


#!/bin/sh
set -e

DJANGO_PORT=${DJANGO_PORT:-3000}
VPN_GATEWAY=${VPN_GATEWAY:-openvpn-client}

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

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Django on port $DJANGO_PORT"
exec python manage.py runserver 0.0.0.0:"$DJANGO_PORT"


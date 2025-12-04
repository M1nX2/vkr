#!/bin/sh
set -e

DJANGO_PORT=${DJANGO_PORT:-3000}
OPENVPN_CONFIG=${OPENVPN_CONFIG:-/app/config/client.ovpn}

run_openvpn() {
  if [ ! -f "$OPENVPN_CONFIG" ]; then
    echo "OpenVPN config $OPENVPN_CONFIG not found, skipping VPN setup."
    return
  fi

  echo "Starting OpenVPN client with config $OPENVPN_CONFIG"
  # Запускаем OpenVPN в фоне и даем ему поднять туннель
  openvpn --config "$OPENVPN_CONFIG" --daemon

  echo "Waiting for tun0 interface..."
  for _ in $(seq 1 30); do
    if ip addr show tun0 >/dev/null 2>&1; then
      echo "tun0 is up."
      return
    fi
    sleep 1
  done

  echo "tun0 interface did not appear in time; continuing anyway."
}

echo "Applying migrations..."
python manage.py migrate --noinput

run_openvpn

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Django on port $DJANGO_PORT"
exec python manage.py runserver 0.0.0.0:"$DJANGO_PORT"


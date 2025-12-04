#!/bin/sh
set -e

OPENVPN_CONFIG=${OPENVPN_CONFIG:-/vpn/client.ovpn}
OPENVPN_ARGS=${OPENVPN_ARGS:-}

if [ ! -f "$OPENVPN_CONFIG" ]; then
  echo "OpenVPN config $OPENVPN_CONFIG not found."
  exit 1
fi

echo "Starting OpenVPN with $OPENVPN_CONFIG"

# Запускаем OpenVPN в фоне
openvpn --config "$OPENVPN_CONFIG" $OPENVPN_ARGS --daemon

# Ждём, пока поднимется tun0
echo "Waiting for tun0 interface..."
for i in $(seq 1 30); do
  if ip addr show tun0 >/dev/null 2>&1; then
    echo "tun0 is up"
    break
  fi
  sleep 1
done

# Настраиваем NAT для пересылки трафика из Docker-сети в VPN
echo "Configuring NAT for VPN routing..."
iptables -t nat -A POSTROUTING -o tun0 -j MASQUERADE
iptables -A FORWARD -i eth0 -o tun0 -j ACCEPT
iptables -A FORWARD -i tun0 -o eth0 -m state --state RELATED,ESTABLISHED -j ACCEPT

echo "VPN gateway is ready"

# Держим контейнер живым
tail -f /dev/null


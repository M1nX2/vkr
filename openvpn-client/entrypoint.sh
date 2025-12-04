#!/bin/sh
set -e

OPENVPN_CONFIG=${OPENVPN_CONFIG:-/vpn/client.ovpn}
OPENVPN_ARGS=${OPENVPN_ARGS:-}

if [ ! -f "$OPENVPN_CONFIG" ]; then
  echo "OpenVPN config $OPENVPN_CONFIG not found."
  exit 1
fi

echo "Starting OpenVPN with $OPENVPN_CONFIG"
exec openvpn --config "$OPENVPN_CONFIG" $OPENVPN_ARGS


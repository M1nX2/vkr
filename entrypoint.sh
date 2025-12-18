#!/bin/sh
# Не прерываем выполнение при ошибках - Django должен запуститься даже если БД недоступна
set +e

DJANGO_PORT=${DJANGO_PORT:-3000}
VPN_GATEWAY=${VPN_GATEWAY:-openvpn-client}
VPN_ROUTES="${VPN_ROUTES:-}"
# Используем переменные окружения из docker-compose напрямую (без значений по умолчанию)
# Значения по умолчанию задаются в docker-compose.yml
DB_HOST="${DB_HOST}"
PYTHON_API_URL="${PYTHON_API_URL}"

# Проверяем, нужно ли настраивать VPN маршруты
# Если VPN_ROUTES задан или DB_HOST/PYTHON_API_URL содержат IP из VPN подсетей
NEED_VPN_ROUTES=false

# Если VPN_ROUTES задан явно, используем его
if [ -n "$VPN_ROUTES" ]; then
  NEED_VPN_ROUTES=true
else
  # Иначе проверяем, содержат ли адреса VPN IP (извлекаем подсети из VPN_ROUTES или используем дефолтные)
  # Извлекаем подсети из VPN_ROUTES для проверки
  VPN_SUBNETS=$(echo "$VPN_ROUTES" | tr ',' '\n' | sed 's|/.*||' | sed 's|\.[0-9]*$|\.|' | sort -u | tr '\n' '|' | sed 's/|$//')
  
  if [ -z "$VPN_SUBNETS" ]; then
    # Если VPN_ROUTES не задан, используем дефолтные паттерны для обратной совместимости
    VPN_SUBNETS="10\.0\.70\.|10\.0\.60\."
  fi
  
  if [ -n "$DB_HOST" ] && echo "$DB_HOST" | grep -qE "^($VPN_SUBNETS)"; then
    NEED_VPN_ROUTES=true
  fi
  
  if [ -n "$PYTHON_API_URL" ] && echo "$PYTHON_API_URL" | grep -qE "($VPN_SUBNETS)"; then
    NEED_VPN_ROUTES=true
  fi
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
    
    # Получаем маршруты из переменной окружения VPN_ROUTES
    VPN_ROUTES="${VPN_ROUTES:-}"
    
    if [ -n "$VPN_ROUTES" ]; then
      # Разбиваем строку по запятым и добавляем каждый маршрут
      echo "$VPN_ROUTES" | tr ',' '\n' | while read -r route; do
        route=$(echo "$route" | xargs)  # Убираем пробелы
        if [ -n "$route" ]; then
          echo "Adding route: $route via $VPN_GATEWAY_IP"
          ip route add "$route" via "$VPN_GATEWAY_IP" 2>/dev/null || echo "Route $route already exists or failed"
        fi
      done
    else
      echo "Warning: VPN_ROUTES not set, skipping route configuration"
    fi
    
    echo "Current routes:"
    ip route
    
    # Проверяем доступность VPN gateway
    echo "Testing VPN gateway connectivity..."
    if ping -c 2 -W 2 $VPN_GATEWAY_IP >/dev/null 2>&1; then
      echo "VPN gateway is reachable"
    else
      echo "Warning: VPN gateway ($VPN_GATEWAY_IP) is not reachable"
    fi
    
    # Если указан PYTHON_API_URL с VPN IP, проверяем доступность бэкенда
    # Извлекаем подсети для проверки
    VPN_SUBNETS_CHECK=$(echo "$VPN_ROUTES" | tr ',' '\n' | sed 's|/.*||' | sed 's|\.[0-9]*$|\.|' | sort -u | tr '\n' '|' | sed 's/|$//')
    if [ -z "$VPN_SUBNETS_CHECK" ]; then
      VPN_SUBNETS_CHECK="10\.0\.70\.|10\.0\.60\."
    fi
    
    if [ -n "$PYTHON_API_URL" ] && echo "$PYTHON_API_URL" | grep -qE "($VPN_SUBNETS_CHECK)"; then
      # Извлекаем IP и порт из URL
      BACKEND_IP=$(echo "$PYTHON_API_URL" | sed -E 's|https?://([^:/]+).*|\1|')
      BACKEND_PORT=$(echo "$PYTHON_API_URL" | sed -E 's|https?://[^:]+:([0-9]+).*|\1|' || echo "8000")
      
      echo "Testing backend connectivity to $BACKEND_IP:$BACKEND_PORT..."
      # Проверяем, можем ли мы достичь IP адреса
      if ping -c 2 -W 2 $BACKEND_IP >/dev/null 2>&1; then
        echo "Backend IP ($BACKEND_IP) is reachable via VPN"
        # Проверяем доступность порта (если установлен nc или curl)
        if command -v nc >/dev/null 2>&1; then
          if nc -z -w 2 $BACKEND_IP $BACKEND_PORT 2>/dev/null; then
            echo "Backend port $BACKEND_PORT is open on $BACKEND_IP"
          else
            echo "Warning: Backend port $BACKEND_PORT is not accessible on $BACKEND_IP"
          fi
        elif command -v curl >/dev/null 2>&1; then
          if curl -s --connect-timeout 2 "http://$BACKEND_IP:$BACKEND_PORT/health" >/dev/null 2>&1; then
            echo "Backend health endpoint is accessible"
          else
            echo "Warning: Backend health endpoint is not accessible on $BACKEND_IP:$BACKEND_PORT"
          fi
        fi
      else
        echo "Warning: Backend IP ($BACKEND_IP) is not reachable via VPN"
        echo "This might indicate:"
        echo "  - Backend is not running on $BACKEND_IP"
        echo "  - VPN tunnel is not properly established"
        echo "  - Firewall is blocking the connection"
      fi
    fi
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


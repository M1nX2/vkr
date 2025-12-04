# Используем официальный образ Python
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    openvpn \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем requirements.txt
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем директории для статики и медиа
RUN mkdir -p /app/staticfiles /app/media

# Настройка прав
RUN chmod +x /app/manage.py /app/entrypoint.sh

# Порт для Django
EXPOSE 3000

ENV DJANGO_PORT=3000

ENTRYPOINT ["/app/entrypoint.sh"]

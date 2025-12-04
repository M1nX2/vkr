# Используем официальный образ Python
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем requirements.txt
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копируем вспомогательные скрипты отдельно, чтобы сохранить права
COPY entrypoint.sh /usr/local/bin/vkr-entrypoint.sh

# Копируем весь проект
COPY . .

# Создаем директории для статики и медиа
RUN mkdir -p /app/staticfiles /app/media

# Настройка прав
RUN chmod +x /app/manage.py /usr/local/bin/vkr-entrypoint.sh

# Порт для Django
EXPOSE 3000

ENV DJANGO_PORT=3000

ENTRYPOINT ["/usr/local/bin/vkr-entrypoint.sh"]

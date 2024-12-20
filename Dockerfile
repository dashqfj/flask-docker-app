FROM python:3.9-slim

WORKDIR /app

# Установка postgresql-client
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Добавляем скрипт для ожидания готовности базы данных
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# Открываем порт
EXPOSE 5000

# По умолчанию запускаем приложение
CMD ["python", "app.py"] 
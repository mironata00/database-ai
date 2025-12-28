# DEPLOY.md - Инструкция по развертыванию

## Быстрый старт (Development)

```bash
# 1. Распаковать архив
tar -xzf database-ai.tar.gz
cd database-ai

# 2. Инициализация
make init
# Отредактировать .env файл

# 3. Запуск
make build
make up
make migrate

# 4. Создать первого администратора
make create-admin

# 5. Проверить
curl http://localhost:8000/health
```

## Production Deployment

### 1. Подготовка сервера

```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установить Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Настроить Elasticsearch limits
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

### 2. Настройка .env для Production

```bash
APP_ENV=production
DEBUG=false

# Сильные пароли
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
MINIO_ROOT_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(openssl rand -base64 32)
ENCRYPTION_KEY=$(openssl rand -base64 32)

# Отключить опасные флаги
DEV_SEED_DATABASE=false
API_RELOAD=false

# Включить все профили для production
```

### 3. SSL/TLS (опционально)

```bash
# Получить сертификаты Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com

# Скопировать в проект
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem

# В .env включить
NGINX_SSL_ENABLED=true
```

### 4. Запуск с полной конфигурацией

```bash
docker-compose --profile replica --profile ha --profile monitoring up -d

# Проверить все контейнеры
docker-compose ps

# Выполнить миграции
docker-compose exec api alembic upgrade head

# Создать администратора
docker-compose exec api python -c "
from app.cli import create_admin_user
import asyncio
asyncio.run(create_admin_user('admin', 'admin@company.ru', 'StrongPass123!'))
"
```

### 5. Резервное копирование

Создать cron задачу:

```bash
sudo crontab -e

# Добавить (ежедневно в 3:00)
0 3 * * * cd /path/to/database-ai && docker-compose exec -T postgres_master pg_dump -U dbai_user database_ai | gzip > backups/db_$(date +\%Y\%m\%d).sql.gz
```

### 6. Мониторинг

После развертывания доступны:
- **Flower**: http://your-server:5555 (username/password из FLOWER_BASIC_AUTH)
- **MinIO Console**: http://your-server:9001
- **API Docs**: http://your-server/docs

### 7. Логи

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f api

# Сохранить логи
docker-compose logs > logs_$(date +%Y%m%d).txt
```

## Troubleshooting

### Проблема: Elasticsearch не стартует

```bash
# Проверить vm.max_map_count
sysctl vm.max_map_count

# Увеличить если нужно
sudo sysctl -w vm.max_map_count=262144
```

### Проблема: Out of memory

```bash
# Уменьшить heap size для ES в .env
ES_HEAP_SIZE=1g

# Уменьшить concurrency для Celery
CELERY_PARSING_CONCURRENCY=1
```

### Проблема: IMAP не работает

```bash
# Для Gmail нужен App Password
# 1. Включить 2FA в Google Account
# 2. Создать App Password
# 3. Использовать его в EMAIL_IMAP_PASSWORD

# Тест подключения
docker-compose exec api python -c "
import imaplib
mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login('your-email@gmail.com', 'your-app-password')
print('SUCCESS')
"
```

## Обновление версии

```bash
# Остановить сервисы
docker-compose down

# Бэкап БД
docker-compose exec postgres_master pg_dump -U dbai_user database_ai > backup_before_update.sql

# Обновить код
git pull origin main

# Пересобрать
docker-compose build

# Запустить и мигрировать
docker-compose up -d
docker-compose exec api alembic upgrade head
```

## Масштабирование

### Увеличение API workers

В docker-compose.yml:

```yaml
api:
  deploy:
    replicas: 3  # Вместо 1
```

### Добавление Celery workers

```yaml
celery_worker_parsing:
  deploy:
    replicas: 4  # Больше воркеров
```

### Использование внешней БД

В .env:

```bash
POSTGRES_HOST=your-rds-endpoint.amazonaws.com
POSTGRES_PORT=5432
# Отключить встроенный PostgreSQL в docker-compose.yml
```

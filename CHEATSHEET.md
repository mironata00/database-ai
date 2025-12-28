# 🚀 Database AI - Шпаргалка

## Быстрая установка

```bash
tar -xzf database-ai-final.tar.gz
cd database-ai
chmod +x quick-start.sh
./quick-start.sh
```

## Доступ к системе

| Сервис | URL | Логин |
|--------|-----|-------|
| Frontend | http://localhost:3000 | admin@company.ru / admin123 |
| API Docs | http://localhost:8000/docs | - |
| MinIO | http://localhost:9001 | minioadmin / minio_strong_password_change_me |

## Основные команды

```bash
# Запуск
docker compose up -d

# Остановка
docker compose down

# Логи
docker compose logs -f api
docker compose logs -f frontend

# Перезапуск
docker compose restart api

# Статус
docker compose ps

# Выполнить команду
docker compose exec api bash
docker compose exec postgres_master psql -U postgres -d database_ai
```

## Структура портов

| Сервис | Внутренний | Внешний (по умолчанию) |
|--------|-----------|----------------------|
| Frontend | 3000 | 3000 |
| API | 8000 | 8000 |
| PostgreSQL | 5432 | 5432 |
| Redis | 6379 | 6379 |
| Elasticsearch | 9200 | 9200 |
| MinIO | 9000 | 9000 |
| MinIO Console | 9001 | 9001 |
| Nginx | 80 | 80 |

## Настройка для VPS

### Myjino или аналогичный хостинг

1. **В панели хостинга:**
   - Пробросить внешний порт → внутренний 3000 (Frontend)
   - Пробросить внешний порт → внутренний 8000 (API)

2. **В .env:**
```bash
FRONTEND_PORT=49349  # ваш внешний порт
API_PORT=49351       # ваш внешний порт
```

3. **Перезапуск:**
```bash
docker compose down
docker compose up -d
```

### Nginx на порту 80

```bash
# Nginx уже настроен в docker-compose.yml
# Frontend: http://ваш-домен.ru
# API: http://ваш-домен.ru/api
```

## Устранение проблем

### Порты заняты
```bash
# В .env изменить
API_PORT=8001
FRONTEND_PORT=3001
# Перезапустить
docker compose down && docker compose up -d
```

### Нехватка памяти
```bash
# В .env
ES_HEAP_SIZE=512m
# Перезапустить
docker compose restart elasticsearch
```

### База не работает
```bash
# Пересоздать
docker compose down -v
docker compose up -d
docker compose exec -T postgres_master psql -U postgres -d database_ai < seed.sql
```

### API не отвечает
```bash
docker compose restart api
docker logs db_ai_api --tail 50
```

### Frontend не загружается
```bash
docker compose restart frontend
docker logs db_ai_frontend --tail 30
```

## Production checklist

```bash
# В .env изменить:
APP_ENV=production
DEBUG=false
SECRET_KEY=новый_ключ  # python -c "import secrets; print(secrets.token_urlsafe(32))"
POSTGRES_PASSWORD=надёжный_пароль
REDIS_PASSWORD=надёжный_пароль
MINIO_ROOT_PASSWORD=надёжный_пароль
```

## Backup

```bash
# PostgreSQL
docker compose exec postgres_master pg_dump -U postgres database_ai > backup_$(date +%Y%m%d).sql

# Восстановление
docker compose exec -T postgres_master psql -U postgres -d database_ai < backup_20241226.sql
```

## Обновление

```bash
git pull
docker compose build
docker compose down
docker compose up -d
docker compose exec api alembic upgrade head
```

## Логи

```bash
# Все сервисы
docker compose logs

# Конкретный сервис
docker compose logs -f api

# Последние 100 строк
docker compose logs --tail=100 api

# С timestamps
docker compose logs --timestamps api
```

## API Endpoints

### Авторизация
- `POST /api/auth/login` - вход
- `POST /api/auth/register` - регистрация
- `POST /api/auth/refresh` - обновить токен

### Поставщики
- `GET /api/suppliers/` - список
- `POST /api/suppliers/` - создать
- `GET /api/suppliers/{id}` - детали
- `PUT /api/suppliers/{id}` - обновить
- `DELETE /api/suppliers/{id}` - удалить

### Поиск
- `GET /api/search/` - поиск товаров
- `GET /api/search/suppliers` - поиск поставщиков
- `GET /api/search/suggest` - автодополнение

## Тестовые данные

### Пользователи
```
admin@company.ru / admin123 (Администратор)
manager@company.ru / manager123 (Менеджер)
```

### Поставщики
- СтройКомплект (ИНН: 7701234567) ⭐ 4.3
- ЭлектроМир (ИНН: 7709876543) ⭐ 4.3
- Рога и Копыта (ИНН: 7700000000) ⭐ 1.0 🚫 BLACKLIST
- ООО (ИНН: 7724422835) ⭐ 0.0

## Полезные ссылки

- [README.md](README.md) - описание проекта
- [QUICK_START.md](QUICK_START.md) - подробная установка
- [CHANGELOG.md](CHANGELOG.md) - история изменений
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Контакты поддержки

- 📧 Email: support@example.com
- 💬 Telegram: @example
- 🐛 GitHub Issues

---

**Database AI** - работает из коробки! 🎉

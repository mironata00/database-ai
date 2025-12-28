# Исправление проблем сборки

## Проблема 1: Конфликт версий pytest
**Ошибка:** `pytest==8.0.0` конфликтует с `pytest-asyncio==0.23.4`

**Решение:** Обновить `back/requirements.txt`

Найти строку:
```
pytest==8.0.0
```

Заменить на:
```
pytest==7.4.4
```

## Проблема 2: Warning "version is obsolete"
**Ошибка:** `version: '3.8'` устарел в docker-compose

**Решение:** Удалить первые 2 строки из `docker-compose.yml`

Было:
```yaml
version: '3.8'

services:
```

Стало:
```yaml
services:
```

## Как применить исправления

### Вариант 1: Вручную
```bash
cd /root/dai

# Исправить requirements.txt
nano back/requirements.txt
# Найти pytest==8.0.0 → заменить на pytest==7.4.4

# Исправить docker-compose.yml
nano docker-compose.yml
# Удалить строку "version: '3.8'"

# Пересобрать
docker compose build
```

### Вариант 2: Автоматически
```bash
cd /root/dai

# Исправить pytest
sed -i 's/pytest==8.0.0/pytest==7.4.4/' back/requirements.txt

# Удалить version
sed -i '/^version:/d' docker-compose.yml

# Пересобрать
docker compose build
```

## После исправления

```bash
# Проверить что исправлено
grep pytest back/requirements.txt
# Должно показать: pytest==7.4.4

grep version docker-compose.yml
# Не должно ничего показать

# Собрать заново
docker compose build

# Запустить
docker compose up -d
```

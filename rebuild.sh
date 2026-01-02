#!/bin/bash

echo "=========================================="
echo "  ПОЛНАЯ ПЕРЕСБОРКА DATABASE AI"
echo "=========================================="

cd /root/database-ai

echo ""
echo "=== ШАГ 1: Останавливаем все контейнеры ==="
docker compose down
echo "✓ Контейнеры остановлены"

echo ""
echo "=== ШАГ 2: Очищаем старые образы и освобождаем место ==="
docker system prune -af --volumes
echo "✓ Старые образы удалены"

echo ""
echo "=== Освобождено места ==="
df -h / | grep -E "Filesystem|/$"

echo ""
echo "=== ШАГ 3: Пересборка образов (с новыми .env) ==="
docker compose build --no-cache
echo "✓ Образы пересобраны"

echo ""
echo "=== ШАГ 4: Запуск контейнеров ==="
docker compose up -d
echo "✓ Контейнеры запущены"

echo ""
echo "=== ШАГ 5: Ожидание запуска сервисов ==="
echo "Ждем PostgreSQL (10 сек)..."
sleep 10

echo "Ждем Redis (5 сек)..."
sleep 5

echo "Ждем Elasticsearch (120 сек - это долго, но нужно)..."
sleep 120

echo "Ждем API и Celery (20 сек)..."
sleep 20

echo ""
echo "=== ШАГ 6: Перезапуск Nginx (обновление IP адресов) ==="
docker restart db_ai_v2_nginx
sleep 5
echo "✓ Nginx перезапущен"

echo ""
echo "=========================================="
echo "  ПРОВЕРКА СИСТЕМЫ"
echo "=========================================="

echo ""
echo "=== Статус всех контейнеров ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "=== Проверка API ==="
docker logs db_ai_v2_api --tail 20 | grep -E "Started|ready|Error" || docker logs db_ai_v2_api --tail 20

echo ""
echo "=== Проверка Celery Email ==="
docker logs db_ai_v2_celery_email --tail 15 | grep -E "ready|Connected" || docker logs db_ai_v2_celery_email --tail 15

echo ""
echo "=== Проверка Elasticsearch ==="
docker logs db_ai_v2_elasticsearch --tail 10 | grep -E "started|ready" || docker logs db_ai_v2_elasticsearch --tail 10

echo ""
echo "=== Health Check API ==="
curl -s http://localhost:49351/health && echo "" || echo "❌ API недоступен"

echo ""
echo "=== Health Check через NGINX ==="
curl -sk https://42b79e5f4529.vps.myjino.ru:49358/health && echo "" || echo "❌ NGINX недоступен"

echo ""
echo "=========================================="
echo "  ✅ ПЕРЕСБОРКА ЗАВЕРШЕНА!"
echo "=========================================="
echo ""
echo "Откройте: https://42b79e5f4529.vps.myjino.ru:49358/"
echo ""
echo "Проверьте:"
echo "  1. Логин работает"
echo "  2. Список поставщиков загружается"
echo "  3. Карусель SMTP работает (отправьте 2-3 запроса цен)"
echo ""

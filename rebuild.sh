#!/bin/bash

echo "=========================================="
echo "  ПЕРЕСБОРКА DATABASE AI"
echo "=========================================="

cd /root/database-ai

echo ""
echo "=== ШАГ 1: Останавливаем контейнеры ==="
docker compose down

echo ""
echo "=== ШАГ 2: Удаляем ТОЛЬКО наши образы (не базовые) ==="
docker images | grep "database-ai.*api\|database-ai.*frontend\|database-ai.*celery" | awk '{print $3}' | xargs -r docker rmi -f

echo ""
echo "=== ШАГ 3: Очищаем dangling ==="
docker system prune -f

echo ""
echo "=== ШАГ 4: Пересборка наших образов ==="
docker compose build --no-cache api frontend celery_worker_email celery_worker_parsing celery_worker_search celery_beat

echo ""
echo "=== ШАГ 5: Запуск ==="
docker compose up -d

echo ""
echo "=== ШАГ 6: Ожидание (2 мин) ==="
sleep 120

echo ""
echo "=== ШАГ 7: Перезапуск Nginx ==="
docker restart db_ai_v2_nginx
sleep 5

echo ""
echo "=== СТАТУС ==="
docker ps --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "=== Health Check ==="
curl -s http://localhost:49351/health && echo "✅ API работает" || echo "❌ API недоступен"

echo ""
echo "✅ ГОТОВО!"

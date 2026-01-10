#!/bin/bash
echo "🔄 Запуск реиндексации ElasticSearch..."

TOKEN=$(curl -s -X POST "http://217.26.28.108/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=info@database-ai.ru&password=admin123" | jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Ошибка: не удалось получить токен"
  exit 1
fi

echo "✅ Токен получен"
echo "📊 Запуск реиндексации..."

curl -s -X POST "http://217.26.28.108/api/admin/reindex-all" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq '.'

echo "✅ Готово!"

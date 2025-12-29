#!/bin/bash

# Скрипт для получения структуры БД из Docker контейнера PostgreSQL
# Использование: ./get_db_structure.sh

echo "=== Получение структуры БД из Docker контейнера ==="
echo ""

# Найти имя контейнера с PostgreSQL
CONTAINER_NAME=$(docker ps --filter "ancestor=postgres" --format "{{.Names}}" | head -n 1)

if [ -z "$CONTAINER_NAME" ]; then
    echo "❌ Контейнер PostgreSQL не найден!"
    echo "Убедитесь, что Docker контейнеры запущены: docker-compose up -d"
    exit 1
fi

echo "✅ Найден контейнер: $CONTAINER_NAME"
echo ""

# Получить имя базы данных из переменных окружения
DB_NAME=$(docker exec $CONTAINER_NAME printenv POSTGRES_DB 2>/dev/null || echo "postgres")
DB_USER=$(docker exec $CONTAINER_NAME printenv POSTGRES_USER 2>/dev/null || echo "postgres")

echo "📊 База данных: $DB_NAME"
echo "👤 Пользователь: $DB_USER"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Получить список всех таблиц
echo "📋 СПИСОК ТАБЛИЦ:"
echo ""
docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_catalog.pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, tablename;
"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Получить структуру каждой таблицы
echo "🏗️  СТРУКТУРА ТАБЛИЦ:"
echo ""

TABLES=$(docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -t -c "
SELECT tablename 
FROM pg_catalog.pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;
")

for table in $TABLES; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📦 Таблица: $table"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "
    SELECT 
        a.attname AS column_name,
        pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
        CASE 
            WHEN a.attnotnull THEN 'NOT NULL'
            ELSE 'NULL'
        END AS nullable,
        CASE 
            WHEN pk.conname IS NOT NULL THEN 'PRIMARY KEY'
            WHEN fk.conname IS NOT NULL THEN 'FOREIGN KEY -> ' || fk.confrelname
            ELSE ''
        END AS constraint_info,
        col_description(a.attrelid, a.attnum) AS description
    FROM pg_attribute a
    LEFT JOIN pg_constraint pk ON pk.conrelid = a.attrelid 
        AND a.attnum = ANY(pk.conkey) 
        AND pk.contype = 'p'
    LEFT JOIN pg_constraint fk ON fk.conrelid = a.attrelid 
        AND a.attnum = ANY(fk.conkey) 
        AND fk.contype = 'f'
    LEFT JOIN pg_class fc ON fc.oid = fk.confrelid
    LEFT JOIN pg_namespace fn ON fn.oid = fc.relnamespace,
        pg_class c
    WHERE c.relname = '$table'
        AND a.attrelid = c.oid
        AND a.attnum > 0
        AND NOT a.attisdropped
    ORDER BY a.attnum;
    "
    
    echo ""
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔗 ВНЕШНИЕ КЛЮЧИ (RELATIONSHIPS):"
echo ""

docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "
SELECT
    tc.table_name AS from_table,
    kcu.column_name AS from_column,
    ccu.table_name AS to_table,
    ccu.column_name AS to_column,
    tc.constraint_name AS constraint_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name, kcu.column_name;
"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "👥 ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ (если существует):"
echo ""

# Проверить наличие таблицы users
HAS_USERS=$(docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -t -c "
SELECT COUNT(*) 
FROM information_schema.tables 
WHERE table_name = 'users';
")

if [ "$HAS_USERS" -gt 0 ]; then
    echo "✅ Таблица 'users' найдена!"
    echo ""
    docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "
    SELECT * FROM users LIMIT 5;
    "
else
    echo "⚠️  Таблица 'users' не найдена"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Анализ структуры БД завершен!"
echo ""
echo "💡 Теперь сохраните этот вывод и отправьте мне для создания файлов менеджеров"
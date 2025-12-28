#!/bin/bash

set -e

echo "================================"
echo "Database AI - Quick Start"
echo "================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is installed${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating .env file from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ .env file created${NC}"
    echo -e "${YELLOW}⚠️  Please review and update .env file with your settings${NC}"
    echo ""
fi

# Build images
echo "🔨 Building Docker images..."
docker compose build

echo ""
echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 30

echo ""
echo "📊 Checking database status..."

# Check if database is ready
until docker compose exec postgres_master pg_isready -U postgres -d database_ai &> /dev/null; do
    echo "Waiting for PostgreSQL to be ready..."
    sleep 2
done

echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
echo ""

# Initialize database with seed data
echo "🌱 Initializing database with seed data..."
if docker compose exec -T postgres_master psql -U postgres -d database_ai < seed.sql; then
    echo -e "${GREEN}✅ Database initialized successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Database initialization failed or already exists${NC}"
    echo "Trying alternative method..."
    docker compose exec api alembic stamp head || true
fi

echo ""
echo "================================"
echo -e "${GREEN}✅ Database AI is ready!${NC}"
echo "================================"
echo ""
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo "MinIO Console: http://localhost:9001"
echo ""
echo -e "${YELLOW}📧 Test Users:${NC}"
echo "  admin@company.ru / admin123 (Admin)"
echo "  manager@company.ru / manager123 (Manager)"
echo ""
echo -e "${YELLOW}📦 Test Suppliers: 4 suppliers loaded${NC}"
echo ""
echo "To view logs: docker compose logs -f"
echo "To stop: docker compose down"
echo ""

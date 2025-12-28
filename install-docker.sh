#!/bin/bash
# Docker Installation Script for Ubuntu 24.04
# Автоматическая установка Docker и Docker Compose

set -e

echo "========================================"
echo "Docker Installation for Ubuntu 24.04"
echo "========================================"
echo ""

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Этот скрипт требует права root."
    echo "Запустите: sudo bash install-docker.sh"
    exit 1
fi

echo "Step 1/6: Обновление системы..."
apt-get update
apt-get upgrade -y

echo ""
echo "Step 2/6: Удаление старых версий Docker (если есть)..."
apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

echo ""
echo "Step 3/6: Установка зависимостей..."
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

echo ""
echo "Step 4/6: Добавление официального GPG ключа Docker..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo ""
echo "Step 5/6: Добавление репозитория Docker..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

echo ""
echo "Step 6/6: Установка Docker..."
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo ""
echo "========================================"
echo "✅ Docker установлен успешно!"
echo "========================================"
echo ""

# Проверка версий
echo "Установленные версии:"
docker --version
docker compose version

echo ""
echo "Настройка Docker..."

# Запуск Docker
systemctl start docker
systemctl enable docker

echo "✓ Docker service запущен и добавлен в автозагрузку"

# Добавление текущего пользователя в группу docker
if [ -n "$SUDO_USER" ]; then
    usermod -aG docker $SUDO_USER
    echo "✓ Пользователь $SUDO_USER добавлен в группу docker"
    echo ""
    echo "⚠️  ВАЖНО: Перелогиньтесь или выполните:"
    echo "   newgrp docker"
    echo "   чтобы работать без sudo"
fi

echo ""
echo "Тест установки Docker..."
docker run --rm hello-world

echo ""
echo "========================================"
echo "✅ Установка завершена!"
echo "========================================"
echo ""
echo "Можете запускать проект:"
echo "  cd database-ai"
echo "  docker compose up -d"
echo ""

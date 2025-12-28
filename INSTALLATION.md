# Установка необходимого ПО

## Что нужно установить

Для работы проекта нужен **только Docker** - всё остальное (PostgreSQL, Elasticsearch, Redis и т.д.) запустится автоматически в контейнерах.

---

## 🐧 Linux (Ubuntu/Debian)

### 1. Обновить систему
```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Установить Docker
```bash
# Удалить старые версии (если есть)
sudo apt remove docker docker-engine docker.io containerd runc

# Установить зависимости
sudo apt install -y ca-certificates curl gnupg lsb-release

# Добавить официальный GPG ключ Docker
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Добавить репозиторий
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установить Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 3. Настроить Docker (опционально)
```bash
# Запуск без sudo
sudo usermod -aG docker $USER
newgrp docker

# Автозапуск при загрузке
sudo systemctl enable docker
sudo systemctl start docker
```

### 4. Проверить установку
```bash
docker --version
# Должно быть: Docker version 24.x.x или выше

docker compose version
# Должно быть: Docker Compose version v2.x.x или выше
```

---

## 🪟 Windows

### Вариант 1: Docker Desktop (рекомендуется)

1. **Скачать Docker Desktop**
   - Перейти на https://www.docker.com/products/docker-desktop/
   - Скачать для Windows
   - Запустить установщик

2. **Включить WSL 2** (если попросит)
   ```powershell
   # В PowerShell от имени администратора
   wsl --install
   ```

3. **Запустить Docker Desktop**
   - Дождаться полного запуска (иконка в трее)
   - При первом запуске может попросить перезагрузку

4. **Проверить установку**
   ```powershell
   docker --version
   docker compose version
   ```

### Вариант 2: Docker в WSL2 (для продвинутых)

1. Установить WSL2
2. Установить Ubuntu из Microsoft Store
3. Следовать инструкции для Linux внутри WSL

---

## 🍎 macOS

### 1. Установить Docker Desktop

1. **Скачать**
   - Перейти на https://www.docker.com/products/docker-desktop/
   - Выбрать версию для Mac (Intel или Apple Silicon)

2. **Установить**
   - Открыть .dmg файл
   - Перетащить Docker в Applications

3. **Запустить Docker Desktop**
   - Открыть из Applications
   - Дождаться запуска

4. **Проверить**
   ```bash
   docker --version
   docker compose version
   ```

---

## ✅ Проверка готовности

После установки Docker выполните:

```bash
# Проверка Docker
docker run hello-world
# Должно вывести "Hello from Docker!"

# Проверка Docker Compose
docker compose version
# Должно показать версию 2.x.x или выше
```

---

## 🚀 Запуск проекта после установки Docker

### Способ 1: Автоматический (самый простой)

```bash
cd database
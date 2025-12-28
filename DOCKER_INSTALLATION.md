# Установка Docker на Ubuntu 24.04 - Пошаговая инструкция

## 🚀 Способ 1: Автоматическая установка (рекомендуется)

```bash
# Запустите скрипт установки
sudo bash install-docker.sh
```

Скрипт автоматически:
- Обновит систему
- Удалит старые версии Docker
- Установит Docker и Docker Compose
- Настроит автозапуск
- Добавит вашего пользователя в группу docker
- Проверит работу

**После установки:**
```bash
# Чтобы работать без sudo, выполните:
newgrp docker

# Или просто перелогиньтесь
exit
# И войдите снова
```

---

## 🛠️ Способ 2: Ручная установка (пошагово)

### Шаг 1: Обновить систему
```bash
sudo apt update
sudo apt upgrade -y
```

### Шаг 2: Удалить старые версии (если есть)
```bash
sudo apt remove docker docker-engine docker.io containerd runc
```

### Шаг 3: Установить зависимости
```bash
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
```

### Шаг 4: Добавить GPG ключ Docker
```bash
sudo install -m 0755 -d /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

### Шаг 5: Добавить репозиторий Docker
```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### Шаг 6: Установить Docker
```bash
sudo apt update

sudo apt install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin
```

### Шаг 7: Запустить Docker
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

### Шаг 8: Добавить пользователя в группу docker
```bash
sudo usermod -aG docker $USER
newgrp docker
```

---

## ✅ Проверка установки

```bash
# Проверить версию Docker
docker --version
# Должно быть: Docker version 27.x.x или выше

# Проверить Docker Compose
docker compose version
# Должно быть: Docker Compose version v2.x.x

# Тест запуска контейнера
docker run hello-world
# Должно вывести "Hello from Docker!"

# Проверить статус сервиса
sudo systemctl status docker
# Должно быть: active (running)
```

---

## 🎯 Что дальше?

После успешной установки Docker:

### 1. Перейти в папку проекта
```bash
cd database-ai
```

### 2. Проверить наличие .env
```bash
ls -la .env
# Если нет - создать:
cp .env.example .env
nano .env  # Отредактировать настройки
```

### 3. Запустить проект

**Вариант A: Автоматически**
```bash
./quick-start.sh
```

**Вариант B: Вручную**
```bash
# Собрать образы
docker compose build

# Запустить сервисы
docker compose up -d

# Подождать 30 секунд
sleep 30

# Выполнить миграции
docker compose exec api alembic upgrade head

# Создать админа
docker compose exec api python -m app.cli create_admin admin admin@test.com Password123!
```

### 4. Проверить что всё работает
```bash
# Список запущенных контейнеров
docker compose ps

# Проверить API
curl http://localhost:8000/health

# Посмотреть логи
docker compose logs -f api
```

---

## 🐛 Устранение проблем

### Проблема: "permission denied" при запуске docker
**Решение:**
```bash
# Добавить себя в группу docker
sudo usermod -aG docker $USER

# Применить изменения
newgrp docker

# Или перелогиниться
exit
# и войти снова
```

### Проблема: "Cannot connect to the Docker daemon"
**Решение:**
```bash
# Запустить Docker
sudo systemctl start docker

# Проверить статус
sudo systemctl status docker

# Если не помогает - перезагрузить
sudo systemctl restart docker
```

### Проблема: Docker занимает много места
**Решение:**
```bash
# Очистить неиспользуемые ресурсы
docker system prune -a

# Посмотреть использование диска
docker system df
```

### Проблема: Порты заняты
**Решение:**
```bash
# Проверить что занимает порт 8000
sudo lsof -i :8000

# Убить процесс
sudo kill -9 <PID>

# Или изменить порт в .env
API_PORT=8001
```

---

## 📚 Полезные команды Docker

```bash
# Список всех контейнеров
docker ps -a

# Остановить все контейнеры
docker stop $(docker ps -aq)

# Удалить все контейнеры
docker rm $(docker ps -aq)

# Список образов
docker images

# Удалить образ
docker rmi <image-id>

# Логи контейнера
docker logs <container-name>

# Войти в контейнер
docker exec -it <container-name> bash

# Статистика использования ресурсов
docker stats
```

---

## 🔗 Ссылки

- [Официальная документация Docker](https://docs.docker.com/)
- [Docker Compose документация](https://docs.docker.com/compose/)
- [Docker Hub](https://hub.docker.com/)

---

## ❓ Часто задаваемые вопросы

**Q: Нужно ли устанавливать Python/PostgreSQL/Redis?**
A: Нет! Всё внутри Docker контейнеров.

**Q: Можно ли использовать Docker Desktop?**
A: Да, но для серверов лучше Docker Engine (из этой инструкции).

**Q: Сколько места займёт Docker?**
A: ~5-10 ГБ для всех образов проекта.

**Q: Как обновить Docker?**
A: `sudo apt update && sudo apt upgrade docker-ce docker-ce-cli`

**Q: Безопасно ли добавлять пользователя в группу docker?**
A: Да для разработки. Для production используйте sudo.

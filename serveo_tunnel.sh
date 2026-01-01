#!/bin/bash
while true; do
  ssh -o ServerAliveInterval=60 -o StrictHostKeyChecking=no -R 80:localhost:80 serveo.net
  echo "Переподключение через 5 секунд..."
  sleep 5
done

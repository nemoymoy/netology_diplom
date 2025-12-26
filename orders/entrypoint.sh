#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    # Если база еще не запущена
    echo "Waiting for postgres..."
    # Проверяем доступность хоста и порта
    while ! nc -z $DJANGO_POSTGRES_HOST $DJANGO_POSTGRES_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi
# Удаляем все старые данные
#python manage.py flush --no-input
# Выполняем миграции
#python manage.py migrate

exec "$@"

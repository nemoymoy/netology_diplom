# образ на основе которого создаём контейнер
FROM python:3.13-alpine3.23

# рабочая директория внутри проекта
WORKDIR /usr/src/app

# переменные окружения для python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# установка зависимостей psycopg2
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev

# устанавливаем зависимости
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

# копируем скрипт проверки запуска postresql entrypoint.sh
COPY entrypoint.sh .

# копируем проект
COPY orders .

# запускаем скрипт entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
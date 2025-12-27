# BUILDER - временный образ с помощью которого будут созданы бинарные файлы Python

# образ на основе которого создаём контейнер
FROM python:3.13-alpine3.23 as builder

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

# проверка кода через линтер
# RUN pip install flake8
COPY . .
# RUN flake8 --ignore=E501,F401 /usr/src/app/orders

COPY requirements.txt .
#RUN pip install -r requirements.txt
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

## копируем проект
#COPY . .
#
## назначаем полномочия для скрипта
#RUN chmod 774 /usr/src/app/entrypoint.sh
#
## запускаем скрипт entrypoint.sh
#ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

# FINAL - копирование файлов в основной образ

FROM python:3.13-alpine3.23

# создаем директорию для пользователя
RUN mkdir -p /home/app

# создаем отдельного пользователя
RUN addgroup -S app && adduser -S app -G app

# создание каталога для приложения
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/static
RUN mkdir $APP_HOME/media
WORKDIR $APP_HOME

# установка зависимостей и копирование из builder
RUN apk update && apk add libpq
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --no-cache /wheels/*

# копирование entrypoint.sh
COPY ./entrypoint.sh $APP_HOME

# копирование проекта Django
COPY . $APP_HOME

# изменение прав для пользователя app
RUN chown -R app:app $APP_HOME

# изменение рабочего пользователя
USER app

# назначаем полномочия для скрипта
RUN chmod 774 /home/app/web/entrypoint.sh

ENTRYPOINT ["/home/app/web/entrypoint.sh"]
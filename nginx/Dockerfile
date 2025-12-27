FROM nginx

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/

# назначаем полномочия для скрипта
RUN chmod 774 /etc/nginx/conf.d/nginx.conf
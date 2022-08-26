FROM python:latest

WORKDIR /usr/src/app

COPY ./flask/requirements.txt ./

COPY ./flask/SCIM ./SCIM
COPY ./flask/uwsgi.ini ./uwsgi.ini
COPY ./start.sh ./start.sh
COPY ./nginx/ssl/scim-server.crt /etc/ssl/certs/scim-server.crt
COPY ./nginx/ssl/scim-server.key /etc/ssl/private/scim-server.key

RUN apt-get clean \
    && apt-get -y update

RUN apt-get -y install nginx \
    && apt-get -y install python3-dev \
    && apt-get -y install build-essential \
    && apt-get install -y dos2unix

RUN pip install --no-cache-dir -r ./requirements.txt

COPY ./nginx/nginx.conf /etc/nginx
RUN dos2unix ./start.sh && apt-get --purge remove -y dos2unix && rm -rf /var/lib/apt/lists/*
RUN chmod +x ./start.sh
RUN chmod o+rw ./SCIM/.cache
CMD ["./start.sh"]
EXPOSE 443
FROM python:3.8-slim
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /code
COPY requirements.txt /code/
RUN apt update && apt install dnsutils netcat iputils-ping traceroute -y 

RUN set -eux && \
    export DEBIAN_FRONTEND=noninteractive && \
    apt-get install -y default-libmysqlclient-dev build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /code/
EXPOSE 8000
WORKDIR /code
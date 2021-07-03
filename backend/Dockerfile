FROM python:3.8-slim
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /code
COPY requirements.txt /code/
RUN apt update && apt install dnsutils netcat traceroute -y 

RUN set -eux && \
    export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get install -y default-libmysqlclient-dev build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /code/
EXPOSE 8000
WORKDIR /code/Uuc_api
CMD bash -c "chmod +x ../migrate_and_setup.sh && ../migrate_and_setup.sh"
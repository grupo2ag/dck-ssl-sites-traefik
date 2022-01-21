FROM python3.8-alpine

COPY requirements.txt /tmp/

RUN apk add --update --no-cache g++ gcc libxslt-dev
RUN pip install -U pip
RUN pip install -r /tmp/requirements.txt

COPY . /app
WORKDIR /app

EXPOSE 80

FROM python:3.10-alpine3.15

ENV PYTHONUNBUFFERED 1
RUN mkdir /scrape_em_all
WORKDIR /scrape_em_all

COPY . /scrape_em_all/
RUN apk add --no-cache --virtual .build-deps \
    ca-certificates gcc postgresql-dev linux-headers musl-dev \
    libffi-dev jpeg-dev zlib-dev 
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
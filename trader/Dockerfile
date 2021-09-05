FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED 1

RUN apt-get update

RUN apt-get install -y netcat

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .
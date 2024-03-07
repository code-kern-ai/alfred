FROM python:3.10-slim

WORKDIR /program

RUN apt-get update && apt-get install -y docker-compose

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY / .

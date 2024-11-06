FROM python:3.12-slim

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --progress-bar off -r /app/requirements.txt

COPY . /app/


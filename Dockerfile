FROM python:3.11-slim-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY .docker.env ./EduTrack/.env

COPY ./script/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

RUN python manage.py collectstatic --noinput

EXPOSE 8000

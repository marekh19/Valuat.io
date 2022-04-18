# pull base image (python and linux version)
FROM python:3.10.4-slim

COPY requirements.txt /app/requirements.txt

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBUG 0

# Configure server
RUN set -ex \
    && apt-get -y update \
    && apt-get -y upgrade \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# set work directory
WORKDIR /app

# copy project
ADD . .

# Collect static files
RUN python manage.py collectstatic --noinput

# EXPOSE 8000
# CMD ["gunicorn", "--bind", ":8000", "--workers", "3", "StockValuation.wsgi:application"]

CMD gunicorn StockValuation.wsgi:application --bind 0.0.0.0:$PORT

FROM python:3.11-slim-bullseye
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache -r /app/requirements.txt
COPY . /app
CMD export LC_ALL="en_US.UTF-8"
CMD dpkg-reconfigure locales
CMD python3 /app/main.py
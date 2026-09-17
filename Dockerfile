FROM python:3.14-slim
LABEL maintainer="andreygomenuk@gmail.com"

ENV PYTHONUNBUFFERED 1

WORKDIR airport_api/

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /files/static

RUN adduser \
    --disabled-password \
    --no-create-home \
    my_user

RUN chown -R my_user /files/static
RUN chmod -R 755 /files/static

USER my_user

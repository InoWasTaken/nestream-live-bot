FROM python:3.9-alpine

RUN pip3 install --user requests

WORKDIR /app

COPY add_webhook_twitch.py ./

ENTRYPOINT ["python3", "add_webhook_twitch.py"]
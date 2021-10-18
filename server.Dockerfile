FROM python:3.9-alpine

RUN apk add gcc musl-dev
RUN pip3 install --user discord.py quart requests

WORKDIR /app
EXPOSE 5000
ENV ENV=prod

COPY server.py ./

ENTRYPOINT python3 server.py

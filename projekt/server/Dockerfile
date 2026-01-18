FROM python:3.11-slim

WORKDIR /app

COPY proj_lib.py .

COPY server/tcp_server.py .

ENV PYTHONUNBUFFERED = 1

ENTRYPOINT ["python", "tcp_server.py"]
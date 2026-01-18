FROM python:3.11-slim

WORKDIR /app

COPY proj_lib.py .

COPY client/tcp_client.py .

ENV SERVER_HOST=tcp_server
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "tcp_client.py"]
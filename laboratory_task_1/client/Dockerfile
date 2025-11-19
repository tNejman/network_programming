FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY udp_client.py .

ENTRYPOINT [ "python3", "udp_client.py" ]
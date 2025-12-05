FROM gcc:latest AS builder

WORKDIR /usr/src/app

COPY udp_client.c . 

RUN apt update && apt install -y libssl-dev
RUN gcc udp_client.c -o udp_client -lssl -lcrypto

FROM debian:stable-slim AS runner

WORKDIR /app

RUN apt update && apt install -y libssl-dev

COPY --from=builder /usr/src/app/udp_client /app/udp_client

ENTRYPOINT [ "./udp_client" ]

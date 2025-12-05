FROM gcc:latest AS builder

WORKDIR /usr/src/app

COPY udp_client.c . 

RUN apt update && apt install -y libssl-dev
RUN gcc udp_client.c -o udp_client -lssl -lcrypto

FROM alpine:latest AS runner

WORKDIR /app

RUN apk update && apk add --no-cache build-base openssl-dev

COPY --from=builder /usr/src/app/udp_client /app/udp_client

ENTRYPOINT [ "./udp_client" ]

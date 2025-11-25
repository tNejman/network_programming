FROM gcc:latest AS builder

WORKDIR /usr/src/app

COPY tcp_client.c . 

RUN gcc -static tcp_client.c -o tcp_client

FROM alpine:latest AS runner

WORKDIR /app

EXPOSE 8888/tcp

COPY --from=builder /usr/src/app/tcp_client /app/tcp_client

ENTRYPOINT [ "./tcp_client" ]

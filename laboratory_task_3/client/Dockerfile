FROM gcc:latest AS builder

WORKDIR /usr/src/app

COPY udp_client.c . 

RUN gcc -static udp_client.c -o udp_client

FROM alpine:latest AS runner

WORKDIR /app

COPY --from=builder /usr/src/app/udp_client /app/udp_client

ENTRYPOINT [ "./udp_client" ]

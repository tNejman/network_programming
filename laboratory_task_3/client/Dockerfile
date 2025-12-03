FROM gcc:latest AS builder

WORKDIR /usr/src/app

COPY udp_client.c . 

RUN sudo apt install libssl-dev
RUN gcc -static udp_client.c -o udp_client -lssl -lcrypto

FROM alpine:latest AS runner

WORKDIR /app

RUN sudo apt install libssl-dev

COPY --from=builder /usr/src/app/udp_client /app/udp_client

ENTRYPOINT [ "./udp_client" ]

FROM gcc:latest AS builder

WORKDIR /usr/src/app

COPY udp_server.c . 

RUN gcc -static udp_server.c -o udp_server

FROM alpine:latest AS runner

WORKDIR /app

EXPOSE 8888/udp

COPY --from=builder /usr/src/app/udp_server /app/udp_server

CMD [ "./udp_server" ]
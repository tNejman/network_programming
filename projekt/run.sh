#!/bin/bash

N_CLIENTS=${1:-1}
NUM_CLIENT_CONTAINERS=${2:-$1}
SERVER_PORT=5000
NET_NAME="z38_network"

trap "echo '--- Shutting down Server ---'; docker rm -f tcp_server >/dev/null 2>&1" EXIT

if grep -qEi "(Microsoft|WSL)" /proc/version; then
    IS_WSL=1
else
    IS_WSL=0
fi

docker rm -f tcp_server $(docker ps -a -q --filter ancestor=tcp_client_img) 2>/dev/null
docker network inspect $NET_NAME >/dev/null 2>&1 || docker network create $NET_NAME
docker build -t tcp_server_img -f server/Dockerfile .
docker build -t tcp_client_img -f client/Dockerfile .
docker run -dit \
    --name tcp_server \
    --network $NET_NAME \
    tcp_server_img $N_CLIENTS

sleep 2
CLIENT_CMD="docker run -it --rm --network $NET_NAME tcp_client_img $SERVER_PORT; read 'Press Enter to close...' var"

for (( i=1; i<=$NUM_CLIENT_CONTAINERS; i++ ))
do   
   if [ "$IS_WSL" -eq 1 ]; then
       cmd.exe /c start "Client $i" wsl.exe bash -c "$CLIENT_CMD"
   else
       if command -v x-terminal-emulator &> /dev/null; then
           x-terminal-emulator -e bash -c "$CLIENT_CMD" &
       elif command -v xterm &> /dev/null; then
           xterm -T "Client $i" -e "bash -c \"$CLIENT_CMD\"" &
       fi
   fi
done

docker attach tcp_server
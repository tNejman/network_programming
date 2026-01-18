#!/bin/bash

N_CLIENTS=${1:-1}
NUM_CLIENT_CONTAINERS=${2:-$1}
SERVER_PORT=5000
NET_NAME="tcp_net"

if grep -qEi "(Microsoft|WSL)" /proc/version; then
    IS_WSL=1
    echo "Detected Environment: WSL"
else
    IS_WSL=0
    echo "Detected Environment: Native Linux"
fi

echo "--- Cleaning up ---"
docker rm -f tcp_server $(docker ps -a -q --filter ancestor=tcp_client_img) 2>/dev/null

docker network inspect $NET_NAME >/dev/null 2>&1 || docker network create $NET_NAME

echo "--- Building ---"
docker build -t tcp_server_img -f server/Dockerfile .
docker build -t tcp_client_img -f client/Dockerfile .

echo "--- Starting Server (Background) ---"
docker run -dit \
    --name tcp_server \
    --network $NET_NAME \
    tcp_server_img $N_CLIENTS

echo "Server started. Waiting 2s..."
sleep 2

echo "--- Launching $NUM_CLIENT_CONTAINERS Clients ---"

CLIENT_CMD="docker run -it --rm --network $NET_NAME tcp_client_img $SERVER_PORT; read -p 'Press Enter to close...' var"

for (( i=1; i<=$NUM_CLIENT_CONTAINERS; i++ ))
do
   echo "Spawning Client $i..."
   
   if [ "$IS_WSL" -eq 1 ]; then
       cmd.exe /c start "Client $i" wsl.exe bash -c "$CLIENT_CMD"
   else
       if command -v x-terminal-emulator &> /dev/null; then
           x-terminal-emulator -e bash -c "$CLIENT_CMD" &
       elif command -v xterm &> /dev/null; then
           xterm -T "Client $i" -e "bash -c \"$CLIENT_CMD\"" &
       else
           echo "ERROR: No terminal emulator found (install xterm or configure x-terminal-emulator)."
       fi
   fi
done

echo "--- Attaching to Server Admin Console ---"
docker attach tcp_server
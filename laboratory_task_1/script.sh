#!/bin/bash

TEAM_PREFIX="z38"
NETWORK_NAME="${TEAM_PREFIX}_network"

VOLUME_NAME="${TEAM_PREFIX}_client_volume"

SERVER_IMAGE_TAG="${TEAM_PREFIX}_udp_server"
CLIENT_IMAGE_TAG="${TEAM_PREFIX}_udp_client"

SERVER_CONTAINER_NAME="${TEAM_PREFIX}_server"
CLIENT_CONTAINER_NAME="${TEAM_PREFIX}_client"

docker volume rm "${VOLUME_NAME}" 2>/dev/null

docker rm -f "${SERVER_CONTAINER_NAME}" 2>/dev/null
docker rm -f "${CLIENT_CONTAINER_NAME}" 2>/dev/null

docker image rm -f "${SERVER_IMAGE_TAG}" 2>/dev/null
docker image rm -f "${CLIENT_IMAGE_TAG}" 2>/dev/null

docker volume create "${VOLUME_NAME}"

docker image build --tag "${SERVER_IMAGE_TAG}" server/

if [ $? -ne 0 ]; then   
    echo "Błąd budowania obrazu serwera"
    exit 1
fi

docker image build --tag "${CLIENT_IMAGE_TAG}" client/

if [ $? -ne 0 ]; then   
    echo "Błąd budowania obrazu klienta"
    exit 1
fi

docker create --name "${SERVER_CONTAINER_NAME}" --network "${NETWORK_NAME}" "${SERVER_IMAGE_TAG}"

if [ $? -ne 0 ]; then   
    echo "Błąd tworzenia kontenera serwera"
    exit 1
fi

docker create \
    --name "${CLIENT_CONTAINER_NAME}" \
    --network "${NETWORK_NAME}" \
    --volume "${VOLUME_NAME}:/images_saved" \
    "${CLIENT_IMAGE_TAG}" "${SERVER_CONTAINER_NAME}"

if [ $? -ne 0 ]; then   
    echo "Błąd tworzenia kontenera klienta"
    exit 1
fi
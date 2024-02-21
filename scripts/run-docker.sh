#!/bin/bash

echo "Push container to GHCR after building? (y/N): "
read -r push

echo "Run container after building? (y/N): "
read -r run_after

if [ "${push}" == 'y' ]; then
  echo "Enter your Github User-Name: "
  read -r usr_name

  if docker login ghcr.io -u "${usr_name}"; then
    echo "Successfully logged in to GHCR!"
  else
    echo "Could not validate credentials."
    exit 1
  fi
fi

yes | docker system prune
docker buildx create --name biosimbuilder --use
docker buildx inspect --bootstrap

if [ "${push}" == 'y' ]; then
  docker buildx build --platform linux/amd64 \
    -t ghcr.io/biosimulators/biosimulator-processes:0.0.1 . \
    --push
else
  docker buildx build --platform linux/amd64 -t ghcr.io/biosimulators/biosimulator-processes:0.0.1 .
fi


if [ "${run_after}" == 'y' ]; then
  docker run --platform linux/amd64 -it -p 8888:8888 ghcr.io/biosimulators/biosimulator-processes:0.0.1
fi

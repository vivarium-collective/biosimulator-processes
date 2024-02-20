#!/bin/bash
yes | docker system prune
docker buildx create --name biosimbuilder --use
docker buildx inspect --bootstrap
docker buildx build --platform linux/amd64 -t biosimulator-processes . \
  && docker run --platform linux/amd64 -it -p 8888:8888 biosimulator-processes

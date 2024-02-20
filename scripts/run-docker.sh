#!/bin/bash
docker buildx create --name biosimbuilder --use
docker buildx inspect --bootstrap
docker buildx build --platform linux/amd64,linux/arm64 -t biosimulator-processes . \
  && docker run -it -p 8888:8888 biosimulator-processes

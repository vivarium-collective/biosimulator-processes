#!/bin/bash
docker buildx create --name biosimbuilder --use
docker buildx inspect --bootstrap
docker buildx build --platform linux/amd64 -t biosimulator-processes . \
  && docker run -it biosimulator-processes

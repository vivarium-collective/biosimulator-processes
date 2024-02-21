#!/bin/bash
yes | docker system prune
docker buildx create --name biosimbuilder --use
docker buildx inspect --bootstrap
docker buildx build --platform linux/amd64 -t biosimulators/biosimulator-processes:0.0.1 . \
  && docker run --platform linux/amd64 -it -p 8888:8888 biosimulator-processes



# FIX REGISTRATION ON INIT
# INCLUDE BUILDER
# GET COMPOSITE?

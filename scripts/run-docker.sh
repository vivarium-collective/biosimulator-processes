#!/bin/bash
docker build -t biosimulator-processes . && docker run -it biosimulator-processes

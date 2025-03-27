#!/usr/bin/env bash
# Wait until worker has opened its gRPC port (example: 50051)
# until nc -z 127.0.0.1 50051; do
#   echo "Waiting for dispatcher..."
#   sleep 1
# done

# until nc -z l 127.0.0.1 6000; do
#   echo "Waiting for runner..."
#   sleep 1
# done



# Run the worker
exec air -c .air.toml
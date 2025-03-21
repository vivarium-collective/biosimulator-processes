# Paths to services
GATEWAY_DIR := gateway
SERVER_DIR := server

# Default target
.PHONY: all
all: run-gateway run-server

# Run gateway with air
.PHONY: run-gateway
run-gateway:
	cd $(GATEWAY_DIR) && air -c air.toml

# Run server with air
.PHONY: run-server
run-server:
	cd $(SERVER_DIR) && air -c air.toml

# Build binaries (optional)
.PHONY: build
build:
	go build -o bin/gateway ./gateway
	go build -o bin/server ./server

# Clean build artifacts
.PHONY: clean
clean:
	rm -rf bin/

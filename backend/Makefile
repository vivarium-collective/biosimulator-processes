CURRENT_DIR := $(shell pwd)
 
GATEWAY_DIR := gateway
SERVER_DIR := server
SHARED_DIR := shared
AIRNAME := .air.toml

.PHONY: all build clean start startGateway startServer startAll stop tidy tidyAll 

all:
	make tidyAll

# deploy: TODO RUN: make dev AND make build AND (remote deploy/push/merge?)
# dev: TODO RUN: tidy expand this to run tidy AND go tests AND python ruff AND pytest 

tidy:
	@[ -n "$(d)" ] && cd "$(d)" && go mod tidy && echo "Go module $(d) is now tidy :)" || echo "Please provide a Go module dirpath to tidy with d=<GO MODULE DIRPATH>"

tidyAll:
	@make tidy d="$(SHARED_DIR)" && make tidy d="$(GATEWAY_DIR)" && make tidy d="$(SERVER_DIR)"

start:
	make startAll

startAll:
	echo "Starting all..." && make startGateway & make startServer & wait
	
startGateway:
	echo "Starting $(GATEWAY_DIR)" && make tidy d="$(GATEWAY_DIR)" && cd "$(GATEWAY_DIR)" && air -c "$(AIRNAME)"  

startServer:
	echo "Starting $(SERVER_DIR)" && make tidy d="$(SERVER_DIR)" && cd "$(SERVER_DIR)" && air -c "$(AIRNAME)"

stop:
	@pkill air || echo "There are no air processes running."

# TODO: use this in container builds
build:
	go build -o bin/gateway ./"$(GATEWAY_DIR)"
	go build -o bin/server ./"$(SERVER_DIR)"
	go build -o bin/shared ./"$(SHARED_DIR)"

clean:
	rm -rf bin/

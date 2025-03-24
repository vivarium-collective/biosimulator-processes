CURRENT_DIR := $(shell pwd)
 
GATEWAY_DIR := gateway
PROTO_DIR := proto
SERVER_DIR := server
SHARED_DIR := shared
AIRNAME := .air.toml


.PHONY: all build clean clear dev docs start startGate startServe startAll stop tidy tidyAll tidyGate 

all:
	make tidyAll


# -- DEVELOPING --#
clear:
	go clean -cache && uv cache prune

dev:
	@# TODO RUN: tidy expand this to run tidy AND go tests AND python ruff AND pytest 
	@make tidyAll && echo "Now running go tests..." && echo "Now running Python lint..." && echo "Now running python tests..."

tidy:
	@[ -n "$(m)" ] \
	&& cd "$(m)" \
	&& go mod tidy \
	&& echo "Go module $(m) is now tidy :)" \
	&& gofmt -w . \
	|| echo "Please provide a Go module dirpath to tidy with d=<GO MODULE DIRPATH>"

tidyAll:
	@make tidy d="$(SHARED_DIR)" && make tidy m="$(PROTO_DIR)" && make docs && make tidy m="$(GATEWAY_DIR)" && make tidy m="$(SERVER_DIR)" 

docs:
	@cd "$(GATEWAY_DIR)" && swag init


# -- RUNNING -- #
start:
	@[ -n "$(m)" ] && cd "$(m)" && make run m="$(m)" || make startAll

run:
	@[ -n "$(m)" ] && cd "$(m)" && air -c "$(AIRNAME)"

startAll:
	echo "Starting all..." && make tidyAll && make startGate & make startServe & wait
	
startgate:
	echo "Starting $(GATEWAY_DIR)" && cd "$(GATEWAY_DIR)" && air -c "$(AIRNAME)"  

startserve:
	echo "Starting $(SERVER_DIR)" && cd "$(SERVER_DIR)" && air -c "$(AIRNAME)"

stop:
	@pkill air || echo "There are no air processes running."


# -- DEPLOYING -- #

build:
	# TODO: use this in container builds
	go build -o gateway/dev ./"$(GATEWAY_DIR)"
	go build -o server/dev ./"$(SERVER_DIR)"
	go build -o shared/dev ./"$(SHARED_DIR)"
	go build -o proto/dev ./"$(PROTO_DIR)"

clean:
	rm -rf dev/

# deploy: TODO RUN: make dev AND make build AND (remote deploy/push/merge?)
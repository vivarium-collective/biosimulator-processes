CURRENT_DIR := $(shell pwd)
 
GATEWAY_DIR := gateway
PROTO_DIR := proto
SERVER_DIR := server
SHARED_DIR := shared
AIRNAME := .air.toml


.PHONY: all
all:
	make tidy


# -- DEVELOPING --#

.PHONY: clean
clear:
	go clean -cache && uv cache prune

.PHONY: dev
dev:
	@# TODO RUN: tidy expand this to run tidy AND go tests AND python ruff AND pytest 
	@make tidy && echo "Now running go tests..." && echo "Now running Python lint..." && echo "Now running python tests..."

.PHONY: tidy
tidy:
	@[ -n "$(m)" ] \
	&& cd "$(m)" \
	&& go mod tidy \
	&& echo "Go module $(m) is now tidy :)" \
	&& gofmt -w . \
	&& echo "Go module $(m) is now formatted :)" \
	|| make tidy-all

.PHONY: tidy-all
tidy-all:
	@make tidy m="$(SHARED_DIR)" && make tidy m="$(PROTO_DIR)" && make docs && make tidy m="$(GATEWAY_DIR)" && make tidy m="$(SERVER_DIR)" 

.PHONY: docs
docs:
	@cd "$(GATEWAY_DIR)" && swag init


# -- RUNNING -- #

.PHONY: up
up:
	echo "Starting all..." && make tidy && make start-air m="$(GATEWAY_DIR)" & make start-air m="$(SERVER_DIR)" & wait

.PHONY: start-air
start-air:
	@[ -n "$(m)" ] && cd "$(m)" && air -c "$(AIRNAME)" || echo "You must pass a module directory"

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
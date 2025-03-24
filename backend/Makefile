CURRENT_DIR := $(shell pwd)
GO_MODULES := gateway server shared proto
GATEWAY_DIR := gateway
DOCS_DIR := "$(GATEWAY_DIR)"/docs
PROTO_DIR := proto
SERVER_DIR := server
SHARED_DIR := shared

PROTOC_GEN = protoc
PROTO_FILES = simulation.proto
GENERATED_PROTO_FILES = proto/simulation.pb.go proto/simulation_grpc.pb.go

AIRNAME := .air.toml

.DEFAULT_GOAL := all


.PHONY: all
all: sync tidy

.PHONY: tidy
tidy:
	@for dir in $(GO_MODULES); do \
		cd "$$dir"; \
		go mod tidy; \
		go fmt ./...; \
		echo "Tidied and formatted $$dir"; \
		cd "$(CURRENT_DIR)"; \
	done

.PHONY: sync
sync:
	@go work sync && echo "go.work is synchronized."

.PHONY: docs
docs:
	@cd "$(GATEWAY_DIR)" && echo "Refreshing docs dir..." && rm -rf docs && mkdir docs && swag init -q --parseDependency --parseInternal && echo "Generated the following files: $(shell ls gateway/docs)"

.PHONY: purge
purge:
	go clean -cache && uv cache prune

.PHONY: mod
mod:
	@[ -n "$(m)" ] && cd "$(m)" && go mod tidy && go fmt ./... && echo "Go module $(m) is now tidy :)"

# -- RUNNING -- #
.PHONY: start
start:
	@[ -n "$(m)" ] && cd "$(m)" && air -log.main_only "true" -c "$(AIRNAME)" || echo "You must pass a module directory"

.PHONY: up
up: sync tidy docs
	@make start m="$(GATEWAY_DIR)" & make start m="$(SERVER_DIR)"

.PHONY: down
down:
	@pkill air || echo "There are no air processes running."

.PHONY: build
build:
	@for dir in $(GO_MODULES); do \
		go build -o "$$dir"/dev ./"$$dir"; \
	done

.PHONY: proto
proto: protoClean
	@echo "Generating protos..." && cd $(PROTO_DIR) && $(PROTOC_GEN) \
		--go_out=. \
		--go_opt=paths=source_relative \
		--go-grpc_out=. \
		--go-grpc_opt=paths=source_relative \
		$(PROTO_FILES)

.PHONY: protoClean
protoClean:
	@echo "removing proto files..." && rm -f $(GENERATED_PROTO_FILES)
# deploy: TODO RUN: make dev AND make build AND (remote deploy/push/merge?)
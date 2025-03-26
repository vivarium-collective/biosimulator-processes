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


.PHONY: tidyall
tidyall:
	@make sync
	@for dir in $(GO_MODULES); do \
		make tidy module="$$dir"; \
	done


.PHONY: tidy
tidy:
	@[ -n "$(module)" ] && cd "$(module)" && go mod tidy && go fmt ./... && echo "Tidied.";

.PHONY: sync
sync:
	@go work sync && echo "go.work is synchronized."

.PHONY: docs
docs:
	@cd gateway && swag init -q --parseDependency --parseInternal

.PHONY: purge
purge:
	go clean -cache && uv cache prune

# -- RUNNING -- #
.PHONY: rungo
rungo: sync tidy
	@[ -n "$(module)" ] && echo ">> STARTING: $(module)" && cd "$(module)" && air -log.main_only "true" -c "$(AIRNAME)" || echo "You must pass a module directory"

.PHONY: gateway
gateway: 
	@make rungo module=gateway

.PHONY: server
server:
	@make rungo module=server

.PHONY: runner
runner:
	uv run uvicorn runner.main:app --reload --host 0.0.0.0 --port=5001

.PHONY: up
up: sync docs tidy 
	@make start m="$(GATEWAY_DIR)" & make start m="$(SERVER_DIR)" & python /Users/alexanderpatrie/Desktop/repos/biosimulator-processes/backend/runner/main.py & wait

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

.PHONY: client
client:
	@cd client && npx vite --open

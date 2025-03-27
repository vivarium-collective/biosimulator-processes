CURRENT_DIR := $(shell pwd)
GO_MODULES := gateway dispatcher worker proto/sim proto/runner
GATEWAY_DIR := gateway
DOCS_DIR := "$(GATEWAY_DIR)"/docs
SIM_PROTO_DIR := proto/sim
RUNNER_PROTO_DIR := proto/runner
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
.PHONY: go
go:
	@[ -n "$(module)" ] && echo ">> STARTING: $(module)" && cd "$(module)" && go mod tidy && air -c "$(AIRNAME)" || echo "You must pass a module directory"

.PHONY: start
start: 
	@make go module=gateway & make go module=dispatcher & python runner/main.py && make go module=worker

.PHONY: down
down:
	@pkill air || echo "There are no air processes running."

.PHONY: build
build:
	@for dir in $(GO_MODULES); do \
		go build -o "$$dir"/dev ./"$$dir"; \
	done

.PHONY: protoGo
protoGo:
	@echo "Generating go protos..." && cd proto/"$(file)" && go mod tidy && $(PROTOC_GEN) \
		--go_out=. \
		--go_opt=paths=source_relative \
		--go-grpc_out=. \
		--go-grpc_opt=paths=source_relative \
		"$(file)".proto

.PHONY: protoPy
protoPy:
	@echo "Generating python protos..."
	@python -m grpc_tools.protoc \
		-I./proto \
		--python_out=. \
		--grpc_python_out=. \
		--proto_path=./proto \
		./proto/runner/runner.proto

.PHONY: protos
protos:
	@make protoGo file=sim && make protoGo file=runner && make protoPy file=sim && make protoPy

.PHONY: protoClean
protoClean:
	@echo "removing proto files..." && rm -f $(GENERATED_PROTO_FILES)
# deploy: TODO RUN: make dev AND make build AND (remote deploy/push/merge?)

.PHONY: client
client:
	@cd client && npx vite --open

.PHONY: gate
gate:
	@uvicorn runner.gateway:app --reload --port 8000 --host 0.0.0.0
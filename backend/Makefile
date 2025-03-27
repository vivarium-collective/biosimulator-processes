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

.PHONY: go
go: sync tidy
	@[ -n "$(module)" ] && echo ">> STARTING: $(module)" && cd "$(module)" && air -c "$(AIRNAME)" || echo "You must pass a module directory"
	

.PHONY: gateway
gateway: 
	@make rungo module=gateway

.PHONY: server
server:
	@make rungo module=server

.PHONY: runner
runner:
	python runner/main.py

.PHONY: up
up: sync 
	@make tidy module=gateway && make tidy module=server && go run gateway/main.go & go run server/main.go & python runner/main.py & wait

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
	@echo "Generating protos..." && cd $(PROTO_DIR)/"$(file)" && $(PROTOC_GEN) \
		--go_out=. \
		--go_opt=paths=source_relative \
		--go-grpc_out=. \
		--go-grpc_opt=paths=source_relative \
		"$(file)".proto

.PHONY: protoPy
protoPy:
	python -m grpc_tools.protoc \
		-I./proto \
		--python_out=. \
		--grpc_python_out=. \
		--proto_path=./proto \
		./proto/"$(file)"/"$(file)".proto


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
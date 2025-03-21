# Makefile

PROTOC_GEN = protoc
PROTO_FILES = simulation.proto
GENERATED_FILES = simulation.pb.go simulation_grpc.pb.go

all:
	$(PROTOC_GEN) \
		--go_out=. \
		--go_opt=paths=source_relative \
		--go-grpc_out=. \
		--go-grpc_opt=paths=source_relative \
		$(PROTO_FILES)

clean:
	rm -f $(GENERATED_FILES)

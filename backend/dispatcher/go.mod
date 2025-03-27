module github.com/vivarium-collective/biosimulator-processes/backend/dispatcher

go 1.24.1

require google.golang.org/grpc v1.71.0

require (
	golang.org/x/net v0.37.0 // indirect
	golang.org/x/sys v0.31.0 // indirect
	golang.org/x/text v0.23.0 // indirect
	google.golang.org/genproto/googleapis/rpc v0.0.0-20250115164207-1a7da9e5054f // indirect
	google.golang.org/protobuf v1.36.6 // indirect
)

replace github.com/vivarium-collective/biosimulator-processes/backend/proto/runner => ../proto/runner

require github.com/vivarium-collective/biosimulator-processes/backend/proto/sim v0.0.0

replace github.com/vivarium-collective/biosimulator-processes/backend/proto/sim => ../proto/sim

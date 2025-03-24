module github.com/vivarium-collective/biosimulator-processes/backend/gateway

go 1.24.1

require (
	github.com/gorilla/mux v1.8.1
	github.com/swaggo/http-swagger v1.3.4
	github.com/swaggo/swag v1.16.4
	github.com/vivarium-collective/biosimulator-processes/backend/proto v0.0.0-20250321190959-a74725061892
	github.com/vivarium-collective/biosimulator-processes/backend/shared v0.0.0-00010101000000-000000000000
	google.golang.org/grpc v1.71.0
)

require (
	github.com/KyleBanks/depth v1.2.1 // indirect
	github.com/go-openapi/jsonpointer v0.19.5 // indirect
	github.com/go-openapi/jsonreference v0.20.0 // indirect
	github.com/go-openapi/spec v0.20.6 // indirect
	github.com/go-openapi/swag v0.19.15 // indirect
	github.com/josharian/intern v1.0.0 // indirect
	github.com/mailru/easyjson v0.7.6 // indirect
	github.com/swaggo/files v0.0.0-20220610200504-28940afbdbfe // indirect
	golang.org/x/net v0.34.0 // indirect
	golang.org/x/sys v0.29.0 // indirect
	golang.org/x/text v0.21.0 // indirect
	golang.org/x/tools v0.21.1-0.20240508182429-e35e4ccd0d2d // indirect
	google.golang.org/genproto/googleapis/rpc v0.0.0-20250115164207-1a7da9e5054f // indirect
	google.golang.org/protobuf v1.36.5 // indirect
	gopkg.in/yaml.v2 v2.4.0 // indirect
)

replace github.com/vivarium-collective/biosimulator-processes/backend/shared => ../shared

replace github.com/vivarium-collective/biosimulator-processes/backend/proto => ../proto

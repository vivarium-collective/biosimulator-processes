// Server

package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"

	pb "github.com/vivarium-collective/biosimulator-processes/backend/proto"
	"google.golang.org/grpc"
	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/types/known/structpb"
)

const (
	localPrefix     string = "http://localhost"
	containerPrefix string = "http://runner"
	port                   = ":50051"
)

var runMode = flag.String("mode", "local", "mode in which to run the main module. One of: local or container") // one of: "local" or "container"
var fastapiPort = flag.Int("port", 5001, "port to which fastapi python runner and go server listen and communicate.")

type server struct {
	pb.UnimplementedSimulatorServer
}

func main() {
	flag.Parse()

	lis, err := net.Listen("tcp", port)
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	grpcServer := grpc.NewServer()
	pb.RegisterSimulatorServer(grpcServer, &server{})

	log.Printf("🚀 gRPC server listening on %s\n", port)
	if err := grpcServer.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}

func (s *server) SubmitSimulation(req *pb.SimulationRequest, stream pb.Simulator_SubmitSimulationServer) error {
	// Prepare request body for FastAPI
	payload := map[string]interface{}{
		"job_id":    req.JobId,
		"timestamp": req.Timestamp,
		"duration":  req.Duration,
		"document":  req.Document, // json.RawMessage(req.State),
	}

	jsonMap := req.Document.AsMap()
	prettyDoc, _ := json.MarshalIndent(jsonMap, "", "  ")
	fmt.Printf("📄 Document:\n%s\n", prettyDoc)

	payloadBytes, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("failed to marshal payload: %w", err)
	}

	// HTTP request to FastAPI
	var fastapiURL string = getFastapiURL(runMode) // Matches FastAPI Docker service name
	fmt.Printf("Using url:\n%v", fastapiURL)
	httpReq, err := http.NewRequest("POST", fastapiURL, bytes.NewBuffer(payloadBytes))
	if err != nil {
		return fmt.Errorf("failed to create FastAPI request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(httpReq)
	fmt.Printf("Got response:\n%v\n", resp)
	if err != nil {
		return fmt.Errorf("FastAPI request failed: %w", err)
	}
	defer resp.Body.Close()

	// Read streamed lines from FastAPI response
	reader := bufio.NewReader(resp.Body)
	for {
		line, err := reader.ReadBytes('\n')
		fmt.Printf("Line:\n%v\n", line)
		if err != nil {
			if err == io.EOF {
				fmt.Print("There was an error")
				break
			}
			return fmt.Errorf("error reading response stream: %w", err)
		}

		// Unmarshal JSON line to a map
		var jsonMap map[string]interface{}
		if err := json.Unmarshal(bytes.TrimSpace(line), &jsonMap); err != nil {
			return fmt.Errorf("error unmarshaling line to map: %w", err)
		}
		fmt.Printf("JSON MAP:\n%v\n", jsonMap)

		// Convert map to structpb.Struct
		structVal, err := structpb.NewStruct(jsonMap)
		if err != nil {
			return fmt.Errorf("error converting map to structpb.Struct: %w", err)
		}

		// Create and stream gRPC response
		res := &pb.SimulationResponse{
			JobId:     req.JobId,
			Status:    "RUNNING:STREAMING",
			Timestamp: req.Timestamp,
			Results:   structVal,
		}

		fmt.Print("The proto:\n")
		debugProto(res)

		err = stream.Send(res)
		// if err := stream.Send(res); err != nil {
		// 	return fmt.Errorf("failed to stream to client: %w", err)
		// }
	}

	return nil
}

func debugProto(msg proto.Message) {
	marshaler := protojson.MarshalOptions{
		Multiline: true,
		Indent:    "  ",
	}
	out, err := marshaler.Marshal(msg)
	if err != nil {
		fmt.Printf("Failed to marshal proto: %v\n", err)
		return
	}
	fmt.Printf("🔍 Proto content:\n%s\n", string(out))
}

func getFastapiURL(runMode *string) string {
	suffix := fmt.Sprintf("%d/simulate", *fastapiPort)
	var prefix string
	switch *runMode {
	case "local":
		prefix = localPrefix
	case "container":
		prefix = containerPrefix
	default:
		prefix = localPrefix
	}
	return fmt.Sprintf("%s:%s", prefix, suffix)
}

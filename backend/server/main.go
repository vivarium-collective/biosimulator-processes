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
	"google.golang.org/protobuf/types/known/structpb"
)

var runMode = flag.String("mode", "local", "mode in which to run the main module. One of: local or container") // one of: "local" or "container"

const (
	fastapiURL      = "http://runner:5000/simulate" // Match FastAPI Docker service name
	fastapiLocalURL = "http://localhost:5000/simulate"
	port            = ":50051"
)

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
		"state":     req.State, // json.RawMessage(req.State),
	}

	payloadBytes, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("failed to marshal payload: %w", err)
	}

	// HTTP request to FastAPI
	var fastapiConn string
	if *runMode == "local" {
		fastapiConn = fastapiLocalURL
	} else {
		fastapiConn = fastapiURL
	}
	httpReq, err := http.NewRequest("POST", fastapiConn, bytes.NewBuffer(payloadBytes))
	if err != nil {
		return fmt.Errorf("failed to create FastAPI request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(httpReq)
	if err != nil {
		return fmt.Errorf("FastAPI request failed: %w", err)
	}
	defer resp.Body.Close()

	// Read streamed lines from FastAPI response
	reader := bufio.NewReader(resp.Body)
	for {
		line, err := reader.ReadBytes('\n')
		if err != nil {
			if err == io.EOF {
				break
			}
			return fmt.Errorf("error reading response stream: %w", err)
		}

		// Unmarshal JSON line to a map
		var jsonMap map[string]interface{}
		if err := json.Unmarshal(bytes.TrimSpace(line), &jsonMap); err != nil {
			return fmt.Errorf("error unmarshaling line to map: %w", err)
		}

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

		if err := stream.Send(res); err != nil {
			return fmt.Errorf("failed to stream to client: %w", err)
		}
	}

	return nil
}

package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"

	pb "github.com/vivarium-collective/biosimulator-processes/backend/proto"
	"google.golang.org/grpc"
)

const (
	fastapiURL = "http://runner:5000/simulate" // Match FastAPI Docker service name
	port       = ":50051"
)

type server struct {
	pb.UnimplementedSimulatorServer
}

func main() {
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
		"job_id":       req.JobId,
		"last_updated": req.LastUpdated,
		"duration":     req.Duration,
		"time_step":    req.TimeStep,
		"spec":         json.RawMessage(req.ConfigJson),
	}

	payloadBytes, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("failed to marshal payload: %w", err)
	}

	// HTTP request to FastAPI
	httpReq, err := http.NewRequest("POST", fastapiURL, bytes.NewBuffer(payloadBytes))
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

		// Create and stream gRPC response
		res := &pb.SimulationResponse{
			JobId:       req.JobId,
			LastUpdated: req.LastUpdated,
			Status:      "streaming",
			ResultJson:  string(bytes.TrimSpace(line)),
			Duration:    req.Duration,
		}

		if err := stream.Send(res); err != nil {
			return fmt.Errorf("failed to stream to client: %w", err)
		}
	}

	return nil
}

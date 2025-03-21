package main

import (
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

// NOTE: this module can be run with:
// make run-server

const fastapiURL = "http://python-simulator:5000/simulate" // adjust to service name

type server struct {
	pb.UnimplementedSimulatorServer
}

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	grpcServer := grpc.NewServer()
	pb.RegisterSimulatorServer(grpcServer, &server{})

	log.Println("🚀 gRPC server listening on :50051")
	if err := grpcServer.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}

func (s *server) SubmitSimulation(req *pb.SimulationRequest, stream pb.Simulator_SubmitSimulationServer) error {
	// Build request to FastAPI
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

	httpReq, err := http.NewRequest("POST", fastapiURL, bytes.NewBuffer(payloadBytes))
	if err != nil {
		return fmt.Errorf("failed to create HTTP request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(httpReq)
	if err != nil {
		return fmt.Errorf("error calling FastAPI: %w", err)
	}
	defer resp.Body.Close()

	buf := make([]byte, 4096)
	decoder := json.NewDecoder(resp.Body)

	for {
		// Decode each JSON object from the stream
		var msg map[string]interface{}
		if err := decoder.Decode(&msg); err != nil {
			if err == io.EOF {
				break
			}
			return fmt.Errorf("stream decode error: %w", err)
		}

		// Marshal back to JSON string to store in the response
		resultBytes, _ := json.Marshal(msg)

		res := &pb.SimulationResponse{
			JobId:       req.JobId,
			LastUpdated: req.LastUpdated,
			Status:      "streaming",
			ResultJson:  string(resultBytes),
			Duration:    req.Duration,
		}

		if err := stream.Send(res); err != nil {
			return fmt.Errorf("failed to stream result: %w", err)
		}
	}

	return nil
}



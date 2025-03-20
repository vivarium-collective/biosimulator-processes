package main

import (
	"context"
	"fmt"
	"log"
	"net"

	"encoding/json"
	"os/exec"

	pb "github.com/myproject/simulation"
	"google.golang.org/grpc"
)

// gRPC Server Implementation
type server struct {
	pb.UnimplementedSimulationServiceServer
}

func (s *server) RunSimulation(ctx context.Context, req *pb.SimulationRequest) (*pb.SimulationResponse, error) {
	log.Println("Received simulation request:", req)

	// Convert request to JSON
	configJSON, _ := json.Marshal(req.Config)

	// Call Python script
	cmd := exec.Command("python3", "run_simulation.py", string(configJSON),
		fmt.Sprintf("%d", req.Duration), fmt.Sprintf("%f", req.TimeStep))
	output, err := cmd.CombinedOutput()
	if err != nil {
		log.Printf("Error running Python simulation: %v\n", err)
		return nil, err
	}

	// Return response
	return &pb.SimulationResponse{Status: "Completed", Results: []string{string(output)}}, nil
}

func main() {
	listener, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("Failed to listen: %v", err)
	}
	grpcServer := grpc.NewServer()
	pb.RegisterSimulationServiceServer(grpcServer, &server{})

	log.Println("Simulation Server running on :50051")
	if err := grpcServer.Serve(listener); err != nil {
		log.Fatalf("Failed to serve: %v", err)
	}
}

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net"

	pb "github.com/vivarium-collective/biosimulator-processes/backend/proto"
	"github.com/vivarium-collective/biosimulator-processes/backend/shared"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
	"google.golang.org/grpc"
)

type server struct {
    pb.UnimplementedSimulatorServer
    db *mongo.Collection
}

func (s *server) SubmitSimulation(ctx context.Context, req *pb.SimulationRequest) (*pb.SimulationResponse, error) {
    var config map[string]interface{}
    if err := json.Unmarshal([]byte(req.ConfigJson), &config); err != nil {
        return nil, fmt.Errorf("invalid config: %w", err)
    }

    doc := shared.SimulationRequest{
        JobID:       req.JobId,
        LastUpdated: req.LastUpdated,
        Duration:    int(req.Duration),
        TimeStep:    req.TimeStep,
        Spec:        config,
        Status:      "submitted",
    }

    _, err := s.db.InsertOne(ctx, doc)
    if err != nil {
        return nil, err
    }

    fmt.Printf("✅ Job %s inserted into Mongo\n", req.JobId)
    return &pb.SimulationResponse{Status: "submitted", JobId: req.JobId}, nil
}

func main() {
    // Connect to Mongo
    mongoClient, err := mongo.Connect(context.Background(), options.Client().ApplyURI("mongodb://mongodb:27017"))
    if err != nil {
        log.Fatal(err)
    }
    collection := mongoClient.Database("bio").Collection("jobs")

    lis, err := net.Listen("tcp", ":50051")
    if err != nil {
        log.Fatalf("failed to listen: %v", err)
    }

    grpcServer := grpc.NewServer()
    pb.RegisterSimulatorServer(grpcServer, &server{db: collection})

    log.Println("🚀 gRPC server listening on :50051")
    if err := grpcServer.Serve(lis); err != nil {
        log.Fatalf("failed to serve: %v", err)
    }
}

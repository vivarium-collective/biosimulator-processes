// server/main.go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"

	pb "github.com/vivarium-collective/biosimulator-processes/backend/proto"
	"google.golang.org/grpc"
	"google.golang.org/protobuf/types/known/structpb"
)

type SimulationJob struct {
	JobID     string
	Timestamp string
	Document  map[string]interface{}
	Duration  int
	ResultCh  chan string 
}

var jobQueue = make(chan SimulationJob, 100)

func main() {
	fmt.Println("🚀 Orchestrator started")

	// Start orchestrator in a goroutine so we can also expose a health check
	startOrchestrator()

	// Simple health check for debugging
	// http.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
	// 	w.WriteHeader(http.StatusOK)
	// 	w.Write([]byte("ok"))
	// })
	// fmt.Println("Health check on :8081/healthz")
	// http.ListenAndServe(":8081", nil)
}


func startOrchestrator() {
	for job := range jobQueue {
		go handleJob(job)
	}
}

func handleJob(job SimulationJob) {
	conn, err := grpc.Dial("localhost:50051", grpc.WithInsecure())
	if err != nil {
		log.Printf("gRPC dial failed: %v", err)
		close(job.ResultCh)
		return
	}
	defer conn.Close()

	client := pb.NewSimulatorClient(conn)
	req := &pb.SimulationRequest{
		JobId:     job.JobID,
		Timestamp: job.Timestamp,
		Duration:  int32(job.Duration),
		Document:  toStructpb(job.Document),
	}

	stream, err := client.SubmitSimulation(context.Background(), req)
	if err != nil {
		log.Printf("Simulation error: %v", err)
		close(job.ResultCh)
		return
	}

	for {
		res, err := stream.Recv()
		if err != nil {
			break
		}
		json, _ := json.Marshal(res)
		job.ResultCh <- string(json)
	}
	close(job.ResultCh)
}

func toStructpb(data map[string]interface{}) *structpb.Struct {
	fmt.Printf("Using data:\n%v\n", data)
	s, err := structpb.NewStruct(data)
	if err != nil {
		log.Fatalf("structpb conversion failed: %v", err)
	}
	return s
}
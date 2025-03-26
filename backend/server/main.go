// server/main.go
package main

import (
	"context"
	"fmt"
	"log"
	"net"

	pb "github.com/vivarium-collective/biosimulator-processes/backend/proto"
	"google.golang.org/grpc"
)

type SimulationJob struct {
	Request  *pb.SimulationRequest
	ResultCh chan *pb.SimulationResponse
}

var jobQueue = make(chan SimulationJob, 100)

type server struct {
	pb.UnimplementedSimulatorServer
}

func (s *server) SubmitJob(ctx context.Context, req *pb.SimulationRequest) (*pb.JobAck, error) {
	resultCh := make(chan *pb.SimulationResponse)
	job := SimulationJob{Request: req, ResultCh: resultCh}
	jobQueue <- job
	go streamToWorker(job)
	return &pb.JobAck{JobId: req.JobId, Status: "QUEUED"}, nil
}

func (s *server) SubmitSimulation(req *pb.SimulationRequest, stream pb.Simulator_SubmitSimulationServer) error {
	resultCh := make(chan *pb.SimulationResponse)
	job := SimulationJob{Request: req, ResultCh: resultCh}
	jobQueue <- job

	for res := range resultCh {
		if err := stream.Send(res); err != nil {
			return err
		}
	}
	return nil
}

func streamToWorker(job SimulationJob) {
	// gRPC to Python runner
	conn, err := grpc.Dial("localhost:50051", grpc.WithInsecure())
	if err != nil {
		log.Printf("Worker gRPC dial failed: %v", err)
		close(job.ResultCh)
		return
	}
	defer conn.Close()

	client := pb.NewSimulatorClient(conn)
	stream, err := client.SubmitSimulation(context.Background(), job.Request)
	if err != nil {
		log.Printf("Worker simulation failed: %v", err)
		close(job.ResultCh)
		return
	}

	for {
		res, err := stream.Recv()
		if err != nil {
			break
		}
		job.ResultCh <- res
	}
	close(job.ResultCh)
}

func main() {
	lis, err := net.Listen("tcp", ":6000") // Gateway talks to Orchestrator here
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}
	s := grpc.NewServer()
	pb.RegisterSimulatorServer(s, &server{})
	fmt.Println("🚀 Orchestrator gRPC running on :6000")
	log.Fatal(s.Serve(lis))
}

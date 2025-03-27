package main

import (
	"log"
	"math/rand"
	"net"
	"sync"
	"time"

	"google.golang.org/grpc"

	sim "github.com/vivarium-collective/biosimulator-processes/backend/proto/sim"
)

type workerStream struct {
	id     string
	stream sim.Simulator_WorkerStreamServer
	ready  chan struct{}
}

type Dispatcher struct {
	sim.UnimplementedSimulatorServer
	mu      sync.Mutex
	workers []*workerStream
}

func (d *Dispatcher) SubmitSimulation(req *sim.SimulationRequest, stream sim.Simulator_SubmitSimulationServer) error {
	d.mu.Lock()
	if len(d.workers) == 0 {
		d.mu.Unlock()
		return nil
	}
	ws := d.workers[rand.Intn(len(d.workers))]
	d.mu.Unlock()

	jobMsg := &sim.WorkerMessage{
		Payload: &sim.WorkerMessage_Job{
			Job: req,
		},
	}

	log.Printf("Dispatching job %s to worker %s", req.JobId, ws.id)
	if err := ws.stream.Send(jobMsg); err != nil {
		return err
	}

	// For demo: stream back progress
	for i := 0; i < 3; i++ {
		res := &sim.SimulationResponse{
			JobId:      req.JobId,
			Timestamp:  time.Now().Format(time.RFC3339),
			Status:     "running",
			IntervalId: int32(i),
			Results:    "Sim step result",
		}
		stream.Send(res)
		time.Sleep(1 * time.Second)
	}

	return nil
}

func (d *Dispatcher) WorkerStream(stream sim.Simulator_WorkerStreamServer) error {
	msg, err := stream.Recv()
	if err != nil {
		return err
	}
	hello := msg.GetHello()
	ws := &workerStream{id: hello.WorkerId, stream: stream, ready: make(chan struct{}, 1)}

	d.mu.Lock()
	d.workers = append(d.workers, ws)
	d.mu.Unlock()

	log.Printf("Worker %s registered", ws.id)

	for {
		msg, err := stream.Recv()
		if err != nil {
			log.Printf("Worker %s disconnected: %v", ws.id, err)
			return err
		}
		if res := msg.GetResult(); res != nil {
			log.Printf("Received result for job %s from %s", res.JobId, ws.id)
		}
	}
}

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	grpcServer := grpc.NewServer()

	dispatcher := &Dispatcher{}
	sim.RegisterSimulatorServer(grpcServer, dispatcher)

	log.Println("Dispatcher listening on :50051")
	if err := grpcServer.Serve(lis); err != nil {
		log.Fatal(err)
	}
}

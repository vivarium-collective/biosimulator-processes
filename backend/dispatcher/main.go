package main

import (
	"context"
	"log"
	"math/rand"
	"net"
	"os"
	"os/signal"
	"sync"
	"syscall"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

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
	streams map[string]sim.Simulator_SubmitSimulationServer // map of JobID -> gRPC stream
}

func NewDispatcher() *Dispatcher {
	return &Dispatcher{
		workers: []*workerStream{},
		streams: make(map[string]sim.Simulator_SubmitSimulationServer),
	}
}

func (d *Dispatcher) SubmitSimulation(req *sim.SimulationRequest, stream sim.Simulator_SubmitSimulationServer) error {
	d.mu.Lock()
	if len(d.workers) == 0 {
		d.mu.Unlock()
		return status.Errorf(codes.Unavailable, "no workers available")
	}

	// Randomly pick a worker
	ws := d.workers[rand.Intn(len(d.workers))]

	// Store client stream by job ID
	d.streams[req.JobId] = stream
	d.mu.Unlock()

	// 🔁 Launch goroutine to detect client disconnection
	go func(jobID string, streamCtx context.Context) {
		<-streamCtx.Done()
		log.Printf("Client stream for job %s canceled", jobID)
		d.mu.Lock()
		delete(d.streams, jobID)
		d.mu.Unlock()
	}(req.JobId, stream.Context())

	// Send job to selected worker
	jobMsg := &sim.WorkerMessage{
		Payload: &sim.WorkerMessage_Job{
			Job: req,
		},
	}

	log.Printf("Dispatching job %s to worker %s", req.JobId, ws.id)
	if err := ws.stream.Send(jobMsg); err != nil {
		log.Printf("Failed to send job to worker: %v", err)
		d.mu.Lock()
		delete(d.streams, req.JobId)
		d.mu.Unlock()
		return err
	}

	return nil
}


func (d *Dispatcher) WorkerStream(stream sim.Simulator_WorkerStreamServer) error {
	msg, err := stream.Recv()
	if err != nil {
		return err
	}

	hello := msg.GetHello()
	ws := &workerStream{
		id:     hello.WorkerId,
		stream: stream,
		ready:  make(chan struct{}, 1),
	}

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
			d.mu.Lock()
			clientStream, ok := d.streams[res.JobId]
			d.mu.Unlock()

			if ok {
				log.Printf("Forwarding result for job %s to gateway", res.JobId)
				if err := clientStream.Send(res); err != nil {
					log.Printf("Failed to send to client: %v", err)
					d.mu.Lock()
					delete(d.streams, res.JobId)
					d.mu.Unlock()
				}				
			} else {
				log.Printf("No active stream for job %s", res.JobId)
			}
		}
	}
}

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	grpcServer := grpc.NewServer()

	dispatcher := NewDispatcher()
	sim.RegisterSimulatorServer(grpcServer, dispatcher)

	log.Println("Dispatcher listening on :50051")
	log.Println(">> DISPATCHER: READY")

	// graceful shutdown
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		sig := <-sigs
		log.Printf("Received signal: %v, shutting down...", sig)
		os.Exit(0)
	}()

	if err := grpcServer.Serve(lis); err != nil {
		log.Fatal(err)
	}
}

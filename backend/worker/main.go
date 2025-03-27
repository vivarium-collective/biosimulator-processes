// package main
//
// import (
//
//	"context"
//	"log"
//	"time"
//
//	"google.golang.org/grpc"
//
//	sim "github.com/vivarium-collective/biosimulator-processes/backend/proto"
//
// )
//
//	func main() {
//		conn, err := grpc.Dial("localhost:50051", grpc.WithInsecure())
//		if err != nil {
//			log.Fatalf("Failed to connect to dispatcher: %v", err)
//		}
//		defer conn.Close()
//
//		client := sim.NewSimulatorClient(conn)
//		stream, err := client.WorkerStream(context.Background())
//		if err != nil {
//			log.Fatalf("Failed to open stream: %v", err)
//		}
//
//		// Register
//		stream.Send(&sim.WorkerMessage{
//			Payload: &sim.WorkerMessage_Hello{
//				Hello: &sim.WorkerHello{WorkerId: "worker-1"},
//			},
//		})
//
//		log.Println("Worker connected. Waiting for jobs...")
//
//		for {
//			msg, err := stream.Recv()
//			if err != nil {
//				log.Fatalf("Stream closed: %v", err)
//			}
//			if job := msg.GetJob(); job != nil {
//				log.Printf("Processing job %s", job.JobId)
//
//				// Simulate processing
//				time.Sleep(time.Duration(job.Duration) * time.Second)
//
//				stream.Send(&sim.WorkerMessage{
//					Payload: &sim.WorkerMessage_Result{
//						Result: &sim.SimulationResponse{
//							JobId:     job.JobId,
//							Timestamp: time.Now().Format(time.RFC3339),
//							Status:    "complete",
//							Results:   "Final result data",
//						},
//					},
//				})
//			}
//		}
//	}
package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"

	"google.golang.org/grpc"

	runnerpb "github.com/vivarium-collective/biosimulator-processes/backend/proto/runner"
	sim "github.com/vivarium-collective/biosimulator-processes/backend/proto/sim"
)

func main() {
	// Connect to dispatcher
	dispatcherConn, err := grpc.Dial("localhost:50051", grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Failed to connect to dispatcher: %v", err)
	}
	defer dispatcherConn.Close()

	dispatcherClient := sim.NewSimulatorClient(dispatcherConn)
	dispatcherStream, err := dispatcherClient.WorkerStream(context.Background())
	if err != nil {
		log.Fatalf("Failed to open stream: %v", err)
	}

	// Register with dispatcher
	dispatcherStream.Send(&sim.WorkerMessage{
		Payload: &sim.WorkerMessage_Hello{
			Hello: &sim.WorkerHello{WorkerId: "worker-python"},
		},
	})
	log.Println("Worker registered with dispatcher")

	// Connect to Python simulation runner
	simConn, err := grpc.Dial("localhost:6000", grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Failed to connect to Python runner: %v", err)
	}
	defer simConn.Close()
	simClient := runnerpb.NewSimulationRunnerClient(simConn)
	pythonStream, err := simClient.RunSimulation(context.Background())
	if err != nil {
		log.Fatalf("Failed to open Python runner stream: %v", err)
	}

	log.Println("Worker connected to Python simulation runner")
	log.Println(">> WORKER: READY")

	// Wait for interrupt to gracefully shutdown
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		sig := <-sigs
		log.Printf("Received signal: %v, shutting down...", sig)
		// gracefully close listeners, etc.
		os.Exit(0)
	}()

	for {
		msg, err := dispatcherStream.Recv()
		if err != nil {
			log.Fatalf("Stream closed: %v", err)
		}
		if job := msg.GetJob(); job != nil {
			log.Printf("Received job: %s", job.JobId)

			// Send job to Python runner
			err := pythonStream.Send(&runnerpb.SimulationJob{
				JobId:    job.JobId,
				Duration: job.Duration,
				Document: job.Document,
			})
			if err != nil {
				log.Printf("Failed to send job to Python: %v", err)
				continue
			}

			// Read streamed results from Python
			go func(jobID string) {
				for {
					result, err := pythonStream.Recv()
					if err != nil {
						log.Printf("Python stream ended for job %s: %v", jobID, err)
						break
					}

					// Forward to dispatcher
					dispatcherStream.Send(&sim.WorkerMessage{
						Payload: &sim.WorkerMessage_Result{
							Result: &sim.SimulationResponse{
								JobId:      result.JobId,
								Timestamp:  result.Timestamp,
								Status:     result.Status,
								IntervalId: result.IntervalId,
								Results:    result.Results,
							},
						},
					})
				}
			}(job.JobId)
		}
	}
}

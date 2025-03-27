package main

import (
	"context"
	"io"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	sim "github.com/vivarium-collective/biosimulator-processes/backend/proto/sim"
	"google.golang.org/grpc"
)

var grpcClient sim.SimulatorClient

func main() {
	conn, err := grpc.Dial("localhost:50051", grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Could not connect to dispatcher: %v", err)
	}
	defer conn.Close()

	grpcClient = sim.NewSimulatorClient(conn)

	router := gin.Default()
	router.Use(cors.Default())
	router.POST("/simulate", simulateHandler)

	log.Println("REST Gateway listening on :8080")
	log.Println(">> GATEWAY: READY")

	// Wait for interrupt to gracefully shutdown
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		sig := <-sigs
		log.Printf("Received signal: %v, shutting down...", sig)
		// gracefully close listeners, etc.
		os.Exit(0)
	}()
	router.Run(":8080")
}

type SimRequestBody struct {
	JobID     string `json:"job_id" binding:"required"`
	Timestamp string `json:"timestamp"` // optional; defaults to now if not provided
	Duration  int32  `json:"duration" binding:"required"`
	Document  string `json:"document" binding:"required"`
}

func simulateHandler(c *gin.Context) {
	var body SimRequestBody
	if err := c.ShouldBindJSON(&body); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if body.Timestamp == "" {
		body.Timestamp = time.Now().Format(time.RFC3339)
	}

	req := &sim.SimulationRequest{
		JobId:     body.JobID,
		Timestamp: body.Timestamp,
		Duration:  body.Duration,
		Document:  body.Document,
	}

	stream, err := grpcClient.SubmitSimulation(context.Background(), req)
	if err != nil {
		c.String(http.StatusInternalServerError, "gRPC error: %v", err)
		return
	}

	c.Writer.Header().Set("Content-Type", "text/event-stream")
	c.Writer.Header().Set("Cache-Control", "no-cache")
	c.Writer.Header().Set("Connection", "keep-alive")

	c.Stream(func(w io.Writer) bool {
		resp, err := stream.Recv()
		if err != nil {
			log.Printf("Stream closed: %v", err)
			return false
		}

		c.SSEvent("simulation", resp)
		return true
	})
}

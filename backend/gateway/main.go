package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"time"

	"github.com/gorilla/mux"
	httpSwagger "github.com/swaggo/http-swagger"
	_ "github.com/vivarium-collective/biosimulator-processes/backend/gateway/docs"
	pb "github.com/vivarium-collective/biosimulator-processes/backend/proto"
	"github.com/vivarium-collective/biosimulator-processes/backend/shared"
	"google.golang.org/grpc"
)

// TODO: ensure that local mode is envoked which changes address paths if so

var mode = flag.String("mode", "local", "mode in which to run the main module. One of: local or container") // one of: "local" or "container"
var debug = flag.Bool("debug", false, "enable debug logging")

const (
	grpcServerAddr      = "server:50051" // 👈 must match Docker Compose service name
	grpcLocalServerAddr = "localhost:50051"
	listenAddr          = "0.0.0.0:8080"
)

var _ shared.SimulationRequest

func main() {
	flag.Parse()

	done := make(chan struct{})

	fmt.Println("🚀 API Gateway running on", listenAddr)
	fmt.Printf("Run Mode: %v\n, Debug: %v\n", *mode, *debug)

	ctxBg := context.Background()

	router := mux.NewRouter()
	router.HandleFunc("/simulate", requestHandler).Methods("POST")

	router.PathPrefix("/swagger/").Handler(httpSwagger.WrapHandler)

	server := &http.Server{
		Addr:    listenAddr,
		Handler: router,
	}

	// Graceful shutdown
	go func() {
		sigint := make(chan os.Signal, 1)
		signal.Notify(sigint, os.Interrupt)
		<-sigint
		fmt.Println("\nShutting down server...")

		if err := server.Shutdown(ctxBg); err != nil {
			log.Fatalf("Server shutdown error: %v", err)
		}
		close(done)
	}()

	if err := server.ListenAndServe(); err != http.ErrServerClosed {
		log.Fatalf("HTTP server error: %v", err)
	}
	<-done
}

// requestHandler godoc
// @Summary      Submit a simulation
// @Description  Accepts a simulation request and streams the results via SSE
// @Accept       json
// @Produce      text/event-stream
// @Param        request body pb.SimulationRequest true "Simulation Input"
// @Success      200 {object} pb.SimulationResponse
// @Failure      400 {string} string "Bad Request"
// @Router       /simulate [post]
func requestHandler(w http.ResponseWriter, r *http.Request) {
	// SSE setup
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming unsupported", http.StatusInternalServerError)
		return
	}

	// Parse the incoming HTTP JSON request
	var simRequest shared.SimulationRequest
	if err := json.NewDecoder(r.Body).Decode(&simRequest); err != nil {
		http.Error(w, "Invalid JSON payload", http.StatusBadRequest)
		return
	}

	// Set up gRPC connection to Go server
	conn, err := grpc.Dial(grpcServerAddr, grpc.WithInsecure())
	if err != nil {
		http.Error(w, "Failed to connect to gRPC server", http.StatusInternalServerError)
		return
	}
	defer conn.Close()

	client := pb.NewSimulatorClient(conn)
	ctx, cancel := context.WithTimeout(context.Background(), time.Minute*5)
	defer cancel()

	req := &pb.SimulationRequest{
		JobId:     simRequest.JobID,
		Timestamp: simRequest.TimeStamp,
		Duration:  int32(simRequest.Duration),
		State:     shared.ToStructpb(simRequest.State),
		Status:    "PENDING:SUBMITTED",
	}

	stream, err := client.SubmitSimulation(ctx, req)
	if err != nil {
		http.Error(w, fmt.Sprintf("gRPC call failed: %v", err), http.StatusInternalServerError)
		return
	}

	for {
		res, err := stream.Recv()
		if err != nil {
			break
		}
		fmt.Fprintf(w, "data: %s\n\n", res.Results)
		flusher.Flush()
	}
}

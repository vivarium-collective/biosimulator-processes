// Gateway
// 1. gene -> ecosike id (translate geneId to ecosikeId) (LLM)
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
	"strconv"
	"time"

	"github.com/gorilla/mux"
	httpSwagger "github.com/swaggo/http-swagger"

	_ "github.com/vivarium-collective/biosimulator-processes/backend/gateway/docs"
	pb "github.com/vivarium-collective/biosimulator-processes/backend/proto"
	"github.com/vivarium-collective/biosimulator-processes/backend/shared"
	"google.golang.org/grpc"
)

const (
	grpcServerAddr      = "server:50051" // 👈 must match Docker Compose service name
	grpcLocalServerAddr = "localhost:50051"
	listenPort          = "8080"
)

var listenAddr = fmt.Sprintf("0.0.0.0:%s", listenPort)
var localSwaggerUrl = fmt.Sprintf("http://localhost:%s/swagger/index.html", listenPort)
var runMode = flag.String("mode", "local", "mode in which to run the main module. One of: local or container") // one of: "local" or "container"
var _ shared.SimulationParams

func main() {
	flag.Parse()

	done := make(chan struct{})

	fmt.Printf("🚀 API Gateway running on port: %s", listenPort)
	if *runMode == "local" {
		fmt.Printf("Swagger documentation is available at: %v", localSwaggerUrl)
	}

	ctxBg := context.Background()

	router := mux.NewRouter()
	router.Use(corsMiddleware)
	router.HandleFunc("/simulate", requestHandler).Methods("POST", "OPTIONS")

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
// @Param duration query int true "Simulation Duration"
// @Param document body object true "Simulation Document"
// @Success      200 {object} pb.SimulationResponse
// @Failure      400 {string} string "Bad Request"
// @Router       /simulate [post]
func requestHandler(w http.ResponseWriter, r *http.Request) {
	// SSE setup
	// @Param        request body shared.SimulationParams true "Simulation Input"
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming unsupported", http.StatusInternalServerError)
		return
	}

	// Set up gRPC connection to Go server
	var grpcAddr string

	if *runMode == "local" {
		grpcAddr = grpcLocalServerAddr
	} else {
		grpcAddr = grpcServerAddr
	}
	fmt.Printf("Using grpc addr: %v", grpcAddr)
	conn, err := grpc.Dial(grpcAddr, grpc.WithInsecure())
	if err != nil {
		http.Error(w, "Failed to connect to gRPC server", http.StatusInternalServerError)
		return
	}
	defer conn.Close()

	client := pb.NewSimulatorClient(conn)
	ctx, cancel := context.WithTimeout(context.Background(), time.Minute*5)
	defer cancel()

	durationStr := r.URL.Query().Get("duration")
	if durationStr == "" {
		// logs clientside in js console
		http.Error(w, "Missing duration", http.StatusBadRequest)
		return
	}
	duration, err := strconv.Atoi(durationStr)
	if err != nil {
		http.Error(w, "Invalid duration value", http.StatusBadRequest)
		return
	}

	// TODO: add this formally to the datamodel
	var payload struct {
		Document map[string]interface{} `json:"document"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		http.Error(w, "Invalid JSON body", http.StatusBadRequest)
		return
	}

	// format proto
	newJobID := shared.NewJobID("simulation")
	timestamp := shared.TimeStamp()
	req := &pb.SimulationRequest{
		JobId:     newJobID,
		Timestamp: timestamp,
		Duration:  int32(duration),
		Document:  shared.ToStructpb(payload.Document),
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

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}

		next.ServeHTTP(w, r)
	})
}

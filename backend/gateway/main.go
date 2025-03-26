package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/google/uuid"
	pb "github.com/vivarium-collective/biosimulator-processes/backend/proto"
	"google.golang.org/grpc"
	"google.golang.org/protobuf/types/known/structpb"
)

func main() {
	http.HandleFunc("/simulate", simulateHandlerWithCORS)
	fmt.Println("🚀 Gateway on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

func simulateHandlerWithCORS(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w)

	if r.Method == http.MethodOptions {
		// Handle preflight CORS request
		w.WriteHeader(http.StatusNoContent)
		return
	}

	simulateHandler(w, r)
}

func simulateHandler(w http.ResponseWriter, r *http.Request) {
	// These headers are also necessary for SSE
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")

	var req struct {
		Document map[string]interface{} `json:"document"`
		Duration int                    `json:"duration"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	jobID := uuid.NewString()
	document, _ := structpb.NewStruct(req.Document)
	simReq := &pb.SimulationRequest{
		JobId:     jobID,
		Timestamp: time.Now().Format(time.RFC3339),
		Duration:  int32(req.Duration),
		Document:  document,
	}

	conn, err := grpc.Dial("localhost:6000", grpc.WithInsecure())
	if err != nil {
		http.Error(w, "Failed to connect to orchestrator", http.StatusInternalServerError)
		return
	}
	defer conn.Close()

	client := pb.NewSimulatorClient(conn)
	stream, err := client.SubmitSimulation(r.Context(), simReq)
	if err != nil {
		http.Error(w, "Simulation failed", http.StatusInternalServerError)
		return
	}

	flusher, _ := w.(http.Flusher)
	for {
		res, err := stream.Recv()
		if err != nil {
			break
		}
		out, _ := json.Marshal(res)
		fmt.Fprintf(w, "data: %s\n\n", out)
		flusher.Flush()
	}
}

func setCORSHeaders(w http.ResponseWriter) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
}

// gateway/main.go

package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/google/uuid"
)

type SimulationJob struct {
	JobID     string
	Timestamp string
	Document  map[string]interface{}
	Duration  int
	ResultCh  chan string // for streaming results
}

var jobQueue = make(chan SimulationJob, 100)

func main() {
	http.HandleFunc("/simulate", simulateHandler)
	fmt.Println("🚀 Gateway listening on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

func simulateHandler(w http.ResponseWriter, r *http.Request) {
	// CORS + SSE headers
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	// Parse request body
	var req struct {
		Document map[string]interface{} `json:"document"`
		Duration int                    `json:"duration"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	jobID := uuid.NewString()
	resultCh := make(chan string)
	job := SimulationJob{
		JobID:     jobID,
		Timestamp: time.Now().Format(time.RFC3339),
		Document:  req.Document,
		Duration:  req.Duration,
		ResultCh:  resultCh,
	}
	jobQueue <- job

	// Stream results
	for msg := range resultCh {
		fmt.Fprintf(w, "data: %s\n\n", msg)
		flusher, _ := w.(http.Flusher)
		flusher.Flush()
	}
}

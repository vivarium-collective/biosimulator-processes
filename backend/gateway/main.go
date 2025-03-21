package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/signal"

	"github.com/vivarium-collective/biosimulator-processes/backend/shared"
)

// NOTE: this module can be run with:
// make run-gateway

var runnerName string = "runner"
var runnerPort int = 5000
var runnerMethod string = "simulate"
var runnerURL string = formatRunnerURL(runnerName, runnerPort, runnerMethod)
var showKeysEscapeChar string = "%+v\n"

func main() {
	const serverAddr = "0.0.0.0:8080" // API Gateway address
	done := make(chan struct{})

	fmt.Println("🚀 API Gateway running on", serverAddr)

	// Graceful shutdown handling
	ctxBg := context.Background()
	router := http.NewServeMux()

	router.HandleFunc("POST /simulate", simulateHandler)

	server := &http.Server{
		Addr:    serverAddr,
		Handler: router,
	}

	// Handle graceful shutdown on SIGINT (Ctrl+C)
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

	// Start the server
	if err := server.ListenAndServe(); err != http.ErrServerClosed {
		log.Fatalf("HTTP server error: %v", err)
	}

	<-done
}

// simulateHandler forwards simulation requests to the Python simulator container
func simulateHandler(w http.ResponseWriter, r *http.Request) {
	// Setup SSE headers
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	// Ensure the writer supports flushing
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming unsupported", http.StatusInternalServerError)
		return
	}

	// Decode incoming JSON payload
	var simRequest shared.SimulationRequest
	if err := json.NewDecoder(r.Body).Decode(&simRequest); err != nil {
		http.Error(w, "Invalid JSON payload", http.StatusBadRequest)
		return
	}

	// Marshal the request and send it to the Python simulator
	requestBody, err := json.Marshal(simRequest)
	if err != nil {
		http.Error(w, "Failed to marshal request", http.StatusInternalServerError)
		return
	}

	req, err := http.NewRequest("POST", runnerURL, bytes.NewBuffer(requestBody))
	if err != nil {
		http.Error(w, "Failed to create request to simulator", http.StatusInternalServerError)
		return
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{
		Timeout: 0, // don't timeout, let the connection stream
	}
	resp, err := client.Do(req)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to reach simulator: %v", err), http.StatusBadGateway)
		return
	}
	defer resp.Body.Close()

	// Stream the response body directly to the client as SSE
	buf := make([]byte, 4096)
	for {
		n, err := resp.Body.Read(buf)
		if n > 0 {
			// Wrap each chunk in SSE format
			fmt.Fprintf(w, "data: %s\n\n", buf[:n])
			flusher.Flush()
		}
		if err != nil {
			if err != io.EOF {
				log.Printf("Stream read error: %v", err)
			}
			break
		}
	}
}

func formatRunnerURL(name string, port int, method string) string {
	return fmt.Sprintf("http://%v:%v/%v", name, port, method)
}



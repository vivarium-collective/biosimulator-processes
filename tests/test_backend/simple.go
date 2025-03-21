package main

import (
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/shirou/gopsutil/v4/cpu"
	"github.com/shirou/gopsutil/v4/mem"
	// "github.com/shirou/gopsutil/v4/cpu"
)

func _main() {
	http.HandleFunc("/events", sseHandler)

	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatalf("Unable to start server:")
	}
}

func sseHandler(w http.ResponseWriter, r *http.Request) {
	// set headers
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	// set memory state ticker(1 time per second)
	memT := time.NewTicker(time.Second)
	defer memT.Stop()

	// set cpu state ticker
	cpuT := time.NewTicker(time.Second)
	defer cpuT.Stop()

	clientDisconnected := r.Context().Done()

	rc := http.NewResponseController(w)

	for {
		select {
		case <-clientDisconnected:
			fmt.Println(">> The client has disconnected!")
		
		// perform mem logic and send mem updates
		case <-memT.C:
			m, err := mem.VirtualMemory()
			if err != nil {
				log.Printf("Unable to get mem: %s", err.Error())
				return
			}

			if _, err := fmt.Fprintf(w, "event:mem\ndata:Total: %d, Used: %d, Perc: %.2f%%\n\n", m.Total, m.Used, m.UsedPercent); 
			err != nil {
				log.Printf("unable to get write", err.Error())
				return 
			}

			rc.Flush()
		
		// perform cpu logic and send cpu updates
		case <-cpuT.C:
			c, err := cpu.Times(false)
			if err != nil {
				log.Printf("Unable to get cpu: %s", err.Error())
				return
			}

			if _, err := fmt.Fprintf(w, "event:cpu\ndata:User: %.2f, System: %.2f, Idle: %.2f\n\n", c[0].User, c[0].System, c[0].Idle); 
			err != nil {
				log.Printf("unable to get write: %s", err.Error())
				return 
			}

			rc.Flush()
		}
	}
}
package main

import (
	"fmt"

	"github.com/vivarium-collective/biosimulator-processes/backend/shared"
)

func main() {
	startingMessage := "Starting Go server..."
	fmt.Printf(">> %+v", startingMessage)
}

func getStateNesting(spec shared.StateDocument, keys ...string) (interface{}, bool) {
	return shared.GetNested(spec)
}
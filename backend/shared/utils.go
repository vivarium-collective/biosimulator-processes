package shared

import (
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/google/uuid"
	"google.golang.org/protobuf/types/known/structpb"
)

func TimeStamp() string {
	return time.Now().Format(time.RFC3339)
}

func NewJobID(scope string) string {
	id := uuid.New() // this generates a UUIDv4
	return fmt.Sprintf("%v-%v", scope, id)
}

func MarshalJSON(data interface{}) string {
	bytes, err := json.Marshal(data)
	if err != nil {
		log.Fatalf("failed to marshal config_json: %v", err)
	}
	return string(bytes)
}

func ToStructpb(data map[string]interface{}) *structpb.Struct {
	s, err := structpb.NewStruct(data)
	if err != nil {
		log.Fatalf("structpb conversion failed: %v", err)
	}
	return s
}

func GetNested(state VivariumDocument, keys ...string) (interface{}, bool) {
	current := interface{}(state)
	for _, k := range keys {
		m, ok := current.(map[string]interface{})
		if !ok {
			return nil, false
		}
		current = m[k]
	}
	return current, true
}

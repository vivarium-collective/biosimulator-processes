package shared

import (
	"encoding/json"
	"log"

	"google.golang.org/protobuf/types/known/structpb"
)

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

func GetNested(document VivariumDocument, keys ...string) (interface{}, bool) {
	current := interface{}(document)
	for _, k := range keys {
		m, ok := current.(map[string]interface{})
		if !ok {
			return nil, false
		}
		current = m[k]
	}
	return current, true
}
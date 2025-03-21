package shared

// in go, you can define type aliases like:
type PayloadBase map[string]interface{}

// Request (client payload) types
type StateDocument = map[string]interface{}

type SimulationRequest struct {
	JobID       string        `json:"job_id"`
	LastUpdated string        `json:"last_updated"`
	Duration    int           `json:"duration"`
	Spec        StateDocument `json:"spec"`
	Status      string       `json:"status"`
}

// Response (server sent events) types
type SimulationResponse struct {
	JobID       string      `json:"job_id"`
	LastUpdated string      `json:"last_updated"`
	Status      string      `json:"status"`
	Result      interface{} `json:"result"` // Can be any type (list, dict, etc.)
	Duration    int         `json:"duration"`
}
package shared

// in go, you can define type aliases like:
type PayloadBase map[string]interface{}

type VivariumDocument map[string]interface{}

type SimulationParams struct {
	TimeStamp string           `json:"timestamp"`
	Duration  int              `json:"duration"`
	Document  VivariumDocument `json:"document"`
}

// Response (server sent events) types
type SimulationResponse struct {
	JobID     string      `json:"job_id"`
	Status    string      `json:"status"`
	TimeStamp string      `json:"timestamp"`
	Results   interface{} `json:"results"`
}

type IntervalResponse struct {
	JobID      string      `json:"job_id"`
	Status     string      `json:"status"`
	TimeStamp  string      `json:"timestamp"`
	Results    interface{} `json:"results"`
	IntervalID int         `json:"interval_id"`
}

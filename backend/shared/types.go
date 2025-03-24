package shared

// in go, you can define type aliases like:
type PayloadBase map[string]interface{}

// Request (client payload) types
type VivariumState map[string]interface{}

type SimulationRequest struct {
	JobID     string        `json:"job_id"`
	TimeStamp string        `json:"timestamp"`
	Duration  int           `json:"duration"`
	State     VivariumState `json:"state"`
	Status    string        `json:"status"`
}

func NewSimulationRequest(
	jobId string,
	timestamp string,
	duration int,
	state VivariumState) SimulationRequest {
	return SimulationRequest{
		JobID:     jobId,
		TimeStamp: timestamp,
		Duration:  duration,
		State:     state,
		Status:    "PENDING:SUBMITTED",
	}
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

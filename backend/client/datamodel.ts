export type NestedRecord = Record<string, any>;

export type VivariumDocument = Record<string, string | NestedRecord | string[] | null>;

export type SimulationRequestParams = {
  duration: number;
  document: VivariumDocument
}
  
export type IntervalResponse = {
    job_id: string;
    timestamp: string;
    status: string;
    results: Record<string, any>;
    interval_id: number;
};

export type Payload = {
  url: string;
  init: RequestInit;
} 
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from biosimulator_processes.copasi_process import CopasiProcess
from process_bigraph import Composite


app = FastAPI()

# Define Pydantic models for request and response bodies
class ProcessConfig(BaseModel):
    model_file: str

class SimulationInput(BaseModel):
    time: float
    floating_species: Dict[str, float]
    model_parameters: Dict[str, float]
    reactions: Dict[str, float]

class SimulationResult(BaseModel):
    time: float
    floating_species: Dict[str, float]

# Initialize global or shared state if necessary
processes = {}

@app.post("/initialize/", response_model=str)
def initialize_process(config: ProcessConfig):
    process_id = "unique_process_id"  # Generate a unique ID for the process
    processes[process_id] = CopasiProcess(config=config.dict())
    return process_id

@app.post("/run/{process_id}", response_model=SimulationResult)
def run_simulation(process_id: str, sim_input: SimulationInput):
    if process_id not in processes:
        raise HTTPException(status_code=404, detail="Process not found")
    result = processes[process_id].update(sim_input.dict(), sim_input.time)
    return result

@app.get("/results/{process_id}", response_model=SimulationResult)
def get_results(process_id: str):
    # This is a placeholder; actual implementation will depend on how results are stored and managed
    if process_id not in processes:
        raise HTTPException(status_code=404, detail="Process not found")
    # Placeholder for result retrieval
    results = {}  # Implement logic to retrieve results for the given process_id
    return results

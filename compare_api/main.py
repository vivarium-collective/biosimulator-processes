import logging
from datetime import datetime
from typing import *
from urllib.parse import unquote

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from compare_api.datamodel import SimulatorComparisonResult, CompositeRunError
from compare_api.internal.composite_doc import create_comparison_document, generate_workflow, run_workflow

# logger for this module
logger = logging.getLogger(__name__)

app = FastAPI(title="compare-api", version="1.0.0")
app.dependency_overrides = {}
# enable cross-origin resource sharing (CORS)
origins = [
    'http://127.0.0.1:4200',
    'http://127.0.0.1:4201',
    'http://127.0.0.1:4202',
    'http://localhost:4200',
    'http://localhost:4201',
    'http://localhost:4202',
    'https://biosimulators.org',
    'https://www.biosimulators.org',
    'https://biosimulators.dev',
    'https://www.biosimulators.dev',
    'https://run.biosimulations.dev',
    'https://run.biosimulations.org',
    'https://biosimulations.dev',
    'https://biosimulations.org',
    'https://bio.libretexts.org',
]
app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello from compare-api!!!"}


@app.post(
    "/run",
    response_model=SimulatorComparisonResult,
    name="Run a Simulator Comparison",
    operation_id="run-comparison",
    responses={
        404: {"description": "Unable to run comparison"}
    }
)
async def run_comparison(
        sbml_model_file_path: str = Query(..., title="SBML Model File Path"),
        simulators: List[str] = Query(..., title="Simulators to Compare"),
        duration: int = Query(..., title="Duration"),
        num_steps: int = Query(..., title="Number of Steps")
) -> SimulatorComparisonResult:
    try:
        document = create_comparison_document(sbml_model_file_path, simulators, duration, num_steps)
        workflow = generate_workflow(document)
        results = await run_workflow(workflow, duration)
        return SimulatorComparisonResult(simulators=simulators, value=results)
    except Exception as e:
        logger.warning(f'failed to run simulator comparison composite: {str(e)}')
        raise HTTPException(status_code=404, detail="Parameters not valid.")

import logging
from datetime import datetime
from typing import *
from urllib.parse import unquote

from fastapi import FastAPI, HTTPException, Query, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from biosimulator_processes.data_model.compare_data_model import ProcessAttributes, ComparisonResults
from compare_api.src.composite_doc import create_comparison_document, generate_workflow, run_workflow


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


@app.get(
    "/get-process-attributes",
    response_model=ProcessAttributes,
    name="Get Process Attributes",
    operation_id="get-process-attributes",
    responses={
        404: {"description": "Unable to get attributes for specified simulator process."}})
async def get_process_attributes(
        process_name: str = Query(..., title="Name of the process type; i.e: copasi, tellurium, etc.")
        ) -> ProcessAttributes:
    try:
        module_name = f'{process_name}_process'
        import_statement = f'biosimulator_processes.processes.{module_name}'
        module_paths = module_name.split('_')
        class_name = module_paths[0].replace(module_name[0], module_name[0].upper())
        class_name += module_paths[0].replace(module_name[0], module_name[0].upper())
        module = __import__(
            import_statement, fromlist=[class_name])

        # Get the class from the module
        bigraph_class = getattr(module, class_name)
        attributes = await ProcessAttributes(
            name=class_name,
            initial_state=bigraph_class.initial_state(),
            inputs=bigraph_class.inputs(),
            outputs=bigraph_class.outputs())
        return attributes
    except Exception as e:
        logger.warning(f'failed to run simulator comparison composite: {str(e)}')
        raise HTTPException(status_code=404, detail="Parameters not valid.")


@app.post(
    "/run-comparison",
    response_model=ComparisonResults,
    name="Run a Simulator Comparison",
    operation_id="run-comparison",
    responses={
        404: {"description": "Unable to run comparison"}})
async def run_comparison(
        sbml_model_file: UploadFile = File(..., title="Upload a File"),
        sbml_model_url: str = Query(None, title="SBML Model Url"),
        simulators: List[str] = Query(..., title="Simulators to Compare"),
        duration: int = Query(..., title="Duration"),
        num_steps: int = Query(..., title="Number of Steps")
) -> ComparisonResults:
    # TODO: Add fallback of biosimulations 1.0 for simulators not yet implemented.
    # TODO: enable remote model file for model path with download
    try:
        model_file_content = await sbml_model_file.read()
        model_file_location = sbml_model_file.filename
        document = create_comparison_document(model_file_location, simulators, duration, num_steps)
        workflow = generate_workflow(document)
        results = await run_workflow(workflow, duration)
        return ComparisonResults(simulators=simulators, value=results)
    except AssertionError as e:
        logger.warning(f'failed to run simulator comparison composite: {str(e)}')
        raise HTTPException(status_code=404, detail="Parameters not valid.")

import logging
from datetime import datetime
from typing import *

from fastapi import FastAPI, HTTPException, Query, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from biosimulator_processes import CORE
from biosimulator_processes.data_model.compare_data_model import (
    ProcessComparisonResult,
    ODEComparisonResult)
from verify_api.data_model import (
    ODEComparison,
    AvailableProcesses,
    ProcessAttributes,
    UploadFileResponse)
from verify_api.src.comparison import ode_comparison, process_comparison
from verify_api.src.composite_doc import upload_sbml_file


# logger for this module
logger = logging.getLogger(__name__)


app = FastAPI(title="verification-api", version="1.0.0")
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
    "/get-available-processes",
    response_model=AvailableProcesses,
    name="Get Available Processes",
    operation_id="get-available-processes",
    responses={
        404: {"description": "Unable to get the available processes."},
        200: {"description": "The available processes."}})
def get_available_processes() -> AvailableProcesses:
    return AvailableProcesses(process_names=CORE.process_registry.list())


@app.post(
    "/get-process-attributes",
    response_model=ProcessAttributes,
    name="Get Process Attributes",
    operation_id="get-process-attributes",
    responses={
        404: {"description": "Unable to get attributes for specified simulator process."}})
async def get_process_attributes(
        biomodel_id: str = Query(..., description="Biomodel identifier"),
        sbml_model_file: UploadFile = File(default=None, description="Valid SBML model file"),
        process_name: str = Query(..., title="Name of the process type; i.e: copasi, tellurium, etc.")
        ) -> ProcessAttributes:
    try:
        module_name = f'{process_name}_process'
        import_statement = f'biosimulator_processes.processes.{module_name}'
        module_paths = module_name.split('_')
        class_name = module_paths[0].replace(module_name[0], module_name[0].upper())
        class_name += module_paths[1].replace(module_paths[1][0], module_paths[1][0].upper())
        module = __import__(
            import_statement, fromlist=[class_name])

        # Get the class from the module
        model_source = biomodel_id or sbml_model_file
        bigraph_class = getattr(module, class_name)
        process = bigraph_class(config={'model': {'model_source': biomodel_id}})

        attributes = ProcessAttributes(
            name=class_name,
            initial_state=process.initial_state(),
            input_schema=process.inputs(),
            output_schema=process.outputs())
        return attributes
    except Exception as e:
        logger.warning(f'failed to run simulator comparison composite: {str(e)}')
        raise HTTPException(status_code=404, detail="Parameters not valid.")


@app.post(
    "/upload-sbml-file",
    response_model=UploadFileResponse,
    name="Upload SBML File",
    operation_id="upload-sbml-file",
    responses={
        404: {"description": "Unable to upload the SBML file."}})
async def upload_sbml_file(sbml_model_file: UploadFile = File(..., description="Valid SBML model file")) -> UploadFileResponse:
    try:
        file_location = await upload_sbml_file(sbml_model_file)
        response_message = f"File saved at {file_location} and processing"
        return UploadFileResponse(message=response_message)
    except HTTPException as e:
        logger.warning(f'File to run model upload: {str(e)}')


@app.post(
    "/run-simulator-composite-comparison",
    response_model=ProcessComparisonResult,
    name="Generate a Comparison of Simulator Process outputs",
    operation_id="run-process-comparison",
    responses={
        404: {"description": "Unable to run comparison"}})
def run_process_comparison(
        biomodel_id: str = Query(..., description="Biomodel ID of to be run by the simulator composite"),
        # sbml_model_file: Optional[UploadFile] = File(..., description="Valid SBML model file to be run by the simulator composite")
        simulators: List[str] = Query(..., description="Simulators to compare within a composition"),
        duration: int = Query(..., description="Duration"),
        num_steps: int = Query(..., description="Number of Steps")
) -> Union[ProcessComparisonResult, HTTPException]:
    # TODO: Finish this.
    # TODO: Add fallback of biosimulations 1.0 for simulators not yet implemented.
    try:
        timestamp = str(datetime.now()).replace(' ', '_').replace(':', '-').replace('.', '-')
        result = process_comparison(biomodel_id=biomodel_id, duration=duration, n_steps=num_steps, timestamp=timestamp)
        raise HTTPException(status_code=404, detail="This feature is not yet implemented.")
    except HTTPException as e:
        # logger.warning(f'failed to run simulator comparison composite: {str(e)}')
        # raise HTTPException(status_code=404, detail="Parameters not valid.")
        return e


@app.post(
    "/run-ode-composite-comparison",
    response_model=ODEComparisonResult,
    name="Run a Simulator Comparison",
    operation_id="run-ode-comparison",
    responses={
        404: {"description": "Unable to run comparison"}})
def run_ode_comparison(
        biomodel_id: str = Query(..., description="Biomodel ID of to be run by the simulator composite"),
        # sbml_model_file: Optional[UploadFile] = File(..., description="Valid SBML model file to be run by the simulator composite")
        duration: int = Query(..., description="Simulation duration"),
        num_steps: int = Query(..., description="Number of steps to be recorded in the simulation"),
) -> ODEComparisonResult:
    # TODO: Add fallback of biosimulations 1.0 for simulators not yet implemented.
    try:
        return ODEComparisonResult(duration=duration, num_steps=num_steps, biomodel_id=biomodel_id)
    except AssertionError as e:
        logger.warning(f'failed to run simulator comparison composite: {str(e)}')
        raise HTTPException(status_code=404, detail="Parameters not valid.")

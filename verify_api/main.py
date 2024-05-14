import logging
import os
from tempfile import NamedTemporaryFile
from datetime import datetime
from typing import *

from debugpy.launcher import output
from fastapi import FastAPI, HTTPException, Query, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from biosimulator_processes import CORE
from biosimulator_processes.data_model.compare_data_model import (
    ProcessAttributes,
    ProcessComparisonResult,
    ODEComparisonResult
)
from verify_api.api_data_model import (
    ODEComparison,
    AvailableProcesses,
    ProcessRegistrationData,
    ODEProcessIntervalResult)
from verify_api.src.comparison import ode_comparison, process_comparison, generate_ode_process_comparison


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
    name="Get a list of available process names that can be called and defined within a composite simulation",
    operation_id="get-available-processes",
    responses={
        404: {"description": "Unable to get the available processes."}})
def get_available_processes() -> AvailableProcesses:
    return AvailableProcesses(process_names=CORE.process_registry.list())


@app.post(
    "/get-process-attributes",
    response_model=ProcessAttributes,
    name="Get Process Attribute data for a given model file",
    operation_id="get-process-attributes",
    responses={
        404: {"description": "Unable to get attributes for specified simulator process."},
        200: {"description": "Successfully retrieved process attributes."}})
async def get_process_attributes(
        process_name: str = Query(..., title="Name of the process type; i.e: copasi, tellurium, etc."),
        sbml_model_file: UploadFile = File(..., title="Valid SBML model file by which to infer process attribute details")
        ) -> ProcessAttributes:
    # Create a temporary file to store the uploaded file
    try:
        # Create a named temporary file (deleted automatically when closed)
        with NamedTemporaryFile(delete=False, suffix=".xml") as temp_file:
            contents = await sbml_model_file.read()
            temp_file.write(contents)
            temp_file.flush()
            temp_file_path = temp_file.name

        # Importing the required class based on the process_name
        module_name = f'{process_name}_process'
        import_statement = f'biosimulator_processes.processes.{module_name}'
        module_paths = module_name.split('_')
        class_name = ''.join(word.capitalize() for word in module_paths)
        module = __import__(import_statement, fromlist=[class_name])

        # Get the class from the module
        bigraph_class = getattr(module, class_name)(config={'model': {'model_source': temp_file_path}})

        attributes = ProcessAttributes(
            name=class_name,
            initial_state=await bigraph_class.initial_state(),
            inputs=await bigraph_class.inputs(),
            outputs=await bigraph_class.outputs())

        # Clean up the temporary file
        os.unlink(temp_file_path)
        return attributes

    except Exception as e:
        # Clean up the temporary file in case of failure before returning the response
        if 'temp_file_path' in locals():
            os.unlink(temp_file_path)
        logger.warning(f'failed to run simulator comparison composite: {str(e)}')
        raise HTTPException(status_code=404, detail="Parameters not valid.")


@app.post(
    "/run-simulator-composite-comparison",
    response_model=ProcessComparisonResult,
    name="Generate a Comparison of Simulator Process outputs",
    operation_id="run-process-comparison",
    responses={
        404: {"description": "Unable to run comparison"}})
def run_process_comparison(
        biomodel_id: str = Query(..., title="Biomodel ID of to be run by the simulator composite"),
        simulators: List[str] = Query(..., title="Simulators to compare within a composition"),
        duration: int = Query(..., title="Duration"),
        num_steps: int = Query(..., title="Number of Steps")
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
    response_model=ODEComparison,
    name="Run an ODE-simulator comparison composition`",
    operation_id="run-ode-comparison",
    responses={
        404: {"description": "Unable to run comparison"}})
async def run_ode_comparison(
        biomodel_id: Optional[str] = Query(default=None, description="Biomodel ID of to be run by the simulator composite"),
        sbml_file: Optional[UploadFile] = File(default=None, description="Valid SBML model file with which to run the ode comparison."),
        duration: int = Query(..., description="Duration of composite simulation"),
        num_steps: int = Query(..., description="Number of Steps"),
) -> ODEComparison:
    # TODO: Add fallback of biosimulations 1.0 for simulators not yet implemented.
    try:
        # handle input entrypoints
        if biomodel_id and sbml_file:
            raise HTTPException(status_code=400, detail="Please provide either a biomodel_id or a model_file, not both.")
        elif biomodel_id is None and sbml_file is None:
            raise HTTPException(status_code=400, detail="Please provide either a biomodel_id or a model_file.")

        # generate a biosimulator processes response
        comparison = await generate_ode_process_comparison(biomodel_id, duration, num_steps)

        # handle conversion of outputs
        comparison_outputs = [
            ODEProcessIntervalResult(
                interval_id=output.interval_id,
                copasi_floating_species_concentrations=output.copasi_floating_species_concentrations,
                tellurium_floating_species_concentrations=output.tellurium_floating_species_concentrations,
                amici_floating_species_concentrations=output.amici_floating_species_concentrations)
            for output in comparison.outputs
        ]

        return ODEComparison(
            duration=comparison.duration,
            num_steps=comparison.num_steps,
            biomodel_id=comparison.biomodel_id,
            timestamp=comparison.timestamp,
            outputs=comparison_outputs)

    except AssertionError as e:
        logger.warning(f'failed to run simulator comparison composite: {str(e)}')
        raise HTTPException(status_code=404, detail="Parameters not valid.")

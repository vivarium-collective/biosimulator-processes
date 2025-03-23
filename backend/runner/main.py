import json
import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

# from backend.runner.processor import JobProcessor
from backend.runner.data_model.requests import SimulationRequest
from backend.runner.data_model.responses import IntervalResponse

import logging
from typing import Any, Mapping

from dotenv import load_dotenv
from vivarium import Vivarium

from backend.runner.processor import JobProcessor
from bsp import app_registrar

from backend.runner.db import MongoConnector
from backend.runner.data_model.responses import SimulationResponse
from backend.runner.handlers import timestamp



app = FastAPI()

# Use a process pool executor for CPU-bound simulations
executor = ProcessPoolExecutor(max_workers=4)


def process_job(job: dict) -> str:
    """Runs one simulation step synchronously and returns JSON."""
    # Run one step (or one duration unit) of simulation
    results = JobProcessor.process_interval(job)
    response = IntervalResponse(results=results)
    return json.dumps(response.serialized)


@app.post("/simulate")
async def simulate(request: Request) -> StreamingResponse:
    body = await request.json()
    payload = SimulationRequest(**body)

    async def event_generator() -> AsyncGenerator:
        loop = asyncio.get_running_loop()

        for _ in range(payload.duration):
            json_result = await loop.run_in_executor(
                executor,
                process_job,
                payload.serialized,
            )
            yield json_result + "\n"

    return StreamingResponse(event_generator(), media_type="application/json")


# CMD [gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.runner.main:app]
import json
import asyncio
import subprocess
from concurrent.futures import ProcessPoolExecutor
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import uvicorn

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
from backend.runner.data_model.responses import IntervalResponse
from backend.runner.handlers import timestamp


RUNNER_PORT = 5001

app = FastAPI()

executor = ProcessPoolExecutor(max_workers=4)


def process_job(job: SimulationRequest, interval_id: int) -> str:
    """Runs one simulation step synchronously and returns JSON."""
    # Run one step (or one duration unit) of simulation
    results = JobProcessor.run_interval(job.document)
    response = IntervalResponse(
        job_id=job.job_id,
        status=job.status,
        timestamp=timestamp(),
        results=results,
        interval_id=interval_id,
    )
    return json.dumps(response.serialized)


# @app.post("/simulate")
# async def simulate(request: Request) -> StreamingResponse:
#     body = await request.json()
#     payload = SimulationRequest(**body)
#     print(f'Got a payload: {payload}')
# 
#     async def event_generator():
#         loop = asyncio.get_running_loop()
#         for interval in range(payload.duration):
#             json_result = await loop.run_in_executor(
#                 executor,
#                 process_job,
#                 payload,
#                 interval
#             )
#             yield f"data: {json_result}\n\n"  # SSE format
# 
#     return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/simulate")
async def simulate(request: Request) -> StreamingResponse:
    body = await request.json()
    payload = SimulationRequest(**body)
    print("Gateway Received:", payload)

    async def event_generator():
        for i in range(body.get("duration", 1)):
            await asyncio.sleep(0.5)
            yield f"processing data for: {{\"step\": {i}}}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# from fastapi import FastAPI, Request
# from fastapi.responses import StreamingResponse
# import asyncio
# 
# app = FastAPI()
# 
# @app.post("/simulate")
# async def simulate(request: Request):
#     body = await request.json()
#     print("🔥 Got request:", body)
# 
#     async def event_generator():
#         for i in range(body.get("duration", 1)):
#             await asyncio.sleep(0.5)
#             yield f"data: {{\"step\": {i}}}\n\n"
# 
#     return StreamingResponse(event_generator(), media_type="text/event-stream")

def format_message(msg, data):
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    RESET = "\033[0m"

    print(f"{BLUE}Gateway Received:\n{RESET} {PURPLE}{data}{RESET}\n")


def spawn_workers():
    try:
        subprocess.run([
            "gunicorn",
            "-w", "4",
            "-k", "uvicorn.workers.UvicornWorker",
            "main:app"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Gunicorn failed with exit code {e.returncode}")


# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=RUNNER_PORT)


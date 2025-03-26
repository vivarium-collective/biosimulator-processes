import json
import asyncio
import os
import subprocess
from concurrent.futures import ProcessPoolExecutor
from typing import AsyncGenerator

import uvicorn
from process_bigraph import pp
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.runner.data_model.requests import SimulationRequest, RequestModel
from backend.runner.data_model.responses import IntervalResponse, ResponseModel
from backend.runner.processor import JobProcessor
from backend.runner.handlers import timestamp


load_dotenv()

RUNNER_PORT = os.getenv('RUNNER_PORT', '5001')

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def process_interval(job: SimulationRequest, interval_id: int) -> ResponseModel:
    """Runs one simulation step synchronously and returns JSON."""
    # Run one step (or one duration unit) of simulation
    results = JobProcessor.run_interval(job.document)
    print(f'Runner.Main >> got results:\n{results}')
    return ResponseModel(
        job_id=job.job_id,
        status=f"STREAMING:{interval_id}",
        timestamp=timestamp(),
        results=results,
        interval_id=interval_id,
    )


async def interval_generator(job: SimulationRequest):
    for i in range(job.duration):
        interval_data = process_interval(job, i)
        yield f"event: intervalResponse\ndata: {interval_data}\n\n"
        await asyncio.sleep(0.5)


@app.post("/simulate")
async def simulate(request: Request) -> StreamingResponse:
    body = await request.json()
    job = SimulationRequest(**body)
    pp(job.serialized)
    return StreamingResponse(interval_generator(job), media_type="text/event-stream")


if __name__ == "__main__":
    uvicorn.run("app", host="0.0.0.0", port=eval(RUNNER_PORT), reload=True)

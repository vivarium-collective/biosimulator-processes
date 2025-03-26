from dataclasses import dataclass
import json
import asyncio
import os
import subprocess
from concurrent.futures import ProcessPoolExecutor
from typing import AsyncGenerator

import uvicorn
from bsp import app_registrar
from vivarium.vivarium import Vivarium
from process_bigraph import pp, ProcessTypes
from fastapi import Body, FastAPI, Query, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.runner.data_model.base import Base, BaseModel
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

core: ProcessTypes = app_registrar.core


def process_interval(viv: Vivarium, job_id: str, interval_id: int):
    """Runs one simulation step synchronously and returns JSON."""
    # Run one step (or one duration unit) of simulation
    results = JobProcessor.run_interval(viv)
    print(f'Runner.Main >> interval response:\n{results}')
    return IntervalResponse(
        job_id=job_id,
        status=f"STREAMING:{interval_id}",
        timestamp=timestamp(),
        results=results,
        interval_id=interval_id,
    )


async def interval_generator(job: SimulationRequest):
    viv = Vivarium(
        processes=core.process_registry.registry,
        types=core.types(),
        core=core,
        document=job.document
    )
    for i in range(job.duration):
        interval_data = json.dumps(
            process_interval(viv, job.job_id, i).serialized
        )
        yield f"event: intervalResponse\ndata: {interval_data}\n\n"
        await asyncio.sleep(0.5)


@app.post("/simulate")
async def simulate(request: Request) -> StreamingResponse:
    body = await request.json()
    job = SimulationRequest(**body)
    # job = SimulationRequest(**body)
    # pp(job.serialized)
    # return StreamingResponse(interval_generator(job), media_type="text/event-stream")
    resp = await perform(document=job.document, duration=job.duration, job_id=job.job_id)
    return resp


class Document(Base):
    state: dict
    composition: dict


@app.post("/perform")
async def perform(
    document: dict,
    duration: int = Query(...),
    job_id: str = Query(...)
):
    job = SimulationRequest(job_id=job_id, timestamp=timestamp(), duration=duration, document=document)
    return StreamingResponse(interval_generator(job), media_type="text/event-stream")



if __name__ == "__main__":
    uvicorn.run("app", host="0.0.0.0", port=eval(RUNNER_PORT), reload=True)

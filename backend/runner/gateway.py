"""
Purely python SSE implementation
"""


from dataclasses import dataclass
import json
import asyncio
import os
from concurrent.futures import ProcessPoolExecutor

import uvicorn
from backend.runner.generate_example import EXAMPLE
from bsp import app_registrar
from vivarium.vivarium import Vivarium
from process_bigraph import pp, ProcessTypes
from fastapi import Body, FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.runner.data_model.base import Base, BaseModel
from backend.runner.data_model.requests import SimulationRequest, RequestModel
from backend.runner.data_model.responses import IntervalResponse, ResponseModel
from backend.runner.handlers import timestamp


load_dotenv()

RUNNER_PORT = os.getenv('RUNNER_PORT', '8000')

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JobProcessor(object):
    @classmethod
    def run_interval(cls, viv: Vivarium) -> dict:
        """Runs a vivarium simulation for an atomic interval index whose range spans a given job's duration"""
        if 'emitter' not in viv.get_state().keys():
            viv.add_emitter()

        viv.run(1)
        results = viv.get_results()
        return results.pop() if isinstance(results, list) else results  # type: ignore
    
    @classmethod
    def process_interval(cls, viv: Vivarium, job_id: str, interval_id: int) -> IntervalResponse:
        """Runs one simulation step synchronously and returns JSON."""
        # Run one step (or one duration unit) of simulation
        results = cls.run_interval(viv)
        return IntervalResponse(
            job_id=job_id,
            status=f"STREAMING:{interval_id}",
            timestamp=timestamp(),
            results=results,
            interval_id=interval_id,
        )
    
    @classmethod
    def test(cls):
        fixtures_path = os.path.join(
            os.path.dirname(
                os.path.dirname(__file__)
            ),
            "fixtures",
            "document.json"
        )
        with open(fixtures_path, 'r') as f:
            document = json.load(f)
        results = JobProcessor.run_interval(document)
        print(f'Got interval results: {results}')


def get_core(source=None) -> ProcessTypes:   
    return app_registrar.core if not source else source


async def interval_generator(job: SimulationRequest, _buffer: float):
    core = get_core()
    viv = Vivarium(
        processes=core.process_registry.registry,
        types=core.types(),
        core=core,
        document=job.document
    )
    for i in range(job.duration):
        result = JobProcessor.process_interval(viv, job.job_id, i).serialized
        interval_data = json.dumps(result)
        yield f"event: intervalResponse\ndata: {interval_data}\n\n"
        await asyncio.sleep(_buffer)


@app.post("/simulate")
async def simulate(
    document: dict = Body(..., example=EXAMPLE),
    duration: int = Query(...),
    job_id: str = Query(...),
    _buffer: float = Query(default=0.5)
) -> StreamingResponse:
    job = SimulationRequest(job_id=job_id, timestamp=timestamp(), duration=duration, document=document)

    # TODO: secure this stream and stream it to a go channel that can be fetched from client with auth
    return StreamingResponse(
        interval_generator(job, _buffer),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


if __name__ == "__main__":
    uvicorn.run("app", host="0.0.0.0", port=eval(RUNNER_PORT), reload=True)

"""
Purely python SSE implementation
"""


from dataclasses import dataclass
import json
import asyncio
import os
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List
import uuid

import uvicorn
from backend.runner.generate_example import EXAMPLE
from bsp import app_registrar
from vivarium.vivarium import Vivarium
from process_bigraph import pp, ProcessTypes
from fastapi import Body, FastAPI, Query, WebSocket
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.runner.data_model.base import Base, BaseModel
from backend.runner.data_model.requests import SimulationRequest, RequestModel
from backend.runner.data_model.responses import IntervalResponse, ResponseModel
from backend.runner.handlers import timestamp


load_dotenv()


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


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        self.active_connections[client_id] = websocket
        print(f"[CONNECT] client_id {client_id} connected")


    def disconnect(self, websocket: WebSocket):
        for cid, ws in list(self.active_connections.items()):
            if ws == websocket:
                del self.active_connections[cid]

    async def send_to(self, client_id: str, message: str):
        websocket = self.active_connections.get(client_id)
        if websocket:
            await websocket.send_text(message)

    async def broadcast(self, message: str):
        for id, connection in self.active_connections.items():
            await connection.send_text(message)


RUNNER_PORT = os.getenv('RUNNER_PORT', '8000')

manager = ConnectionManager()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        result = JobProcessor.process_interval(viv, job.job_id, i)
        interval_data = result.serialized

        # if it's a dict, dump it
        if isinstance(interval_data, dict):
            yield json.dumps(interval_data)
        else:
            yield interval_data  # already JSON

        await asyncio.sleep(_buffer)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_id = str(uuid.uuid4())

    # ✅ Register with manager
    await manager.connect(client_id, websocket)

    # ✅ Let client know its ID
    await websocket.send_text(f"connected:{client_id}")

    try:
        while True:
            await websocket.receive_text()
    except:
        manager.disconnect(websocket)


@app.post("/simulate")
async def simulate(
    document: dict = Body(...),
    duration: int = Query(...),
    job_id: str = Query(...),
    client_id: str = Query(...),
    _buffer: float = Query(default=0.5),
):
    job = SimulationRequest(job_id=job_id, timestamp=timestamp(), duration=duration, document=document)

    async def websocket_result_stream():
        async for update in interval_generator(job, _buffer):
            print(f'Got update:\n{update}')
            await manager.send_to(client_id, update)

    asyncio.create_task(websocket_result_stream())  # run in background
    return {"status": "simulation started", "job_id": job_id}


# @app.post("/simulate")
# async def simulate(
#     document: dict = Body(..., example=EXAMPLE),
#     duration: int = Query(...),
#     job_id: str = Query(...),
#     _buffer: float = Query(default=0.5)
# ) -> StreamingResponse:
#     job = SimulationRequest(job_id=job_id, timestamp=timestamp(), duration=duration, document=document)
# 
#     # TODO: secure this stream and stream it to a go channel that can be fetched from client with auth
#     return StreamingResponse(
#         interval_generator(job, _buffer),
#         media_type="text/event-stream",
#         headers={
#             "Cache-Control": "no-cache",
#             "Connection": "keep-alive"
#         }
#     )


if __name__ == "__main__":
    uvicorn.run("app", host="0.0.0.0", port=eval(RUNNER_PORT), reload=True)

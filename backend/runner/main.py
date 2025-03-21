import json
import time
import asyncio

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

from backend.runner.processor import JobProcessor
from backend.runner.data_model.requests import SimulationRequest
from backend.runner.data_model.responses import SimulationResponse


HOST = "0.0.0.0"
PORT = 5000

app = FastAPI()


# TODO: pass the for loop back to the go server such that this function ONLY represents a single interval's atomic simulation result
async def stream_simulation(payload: SimulationRequest):
    async def event_generator():
        for _ in range(payload.duration):
            response: SimulationResponse = await JobProcessor.process_job(payload.serialized, streaming=True)
            yield json.dumps(response.serialized) + "\n"
            await asyncio.sleep(1)
    return event_generator


@app.post("/simulate")
async def simulate(request: Request) -> StreamingResponse:
    body = await request.json()
    payload = SimulationRequest(**body)
    return StreamingResponse(await stream_simulation(payload), media_type="application/json")


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)

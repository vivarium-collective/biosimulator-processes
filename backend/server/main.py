import json 
import time

from flask import Flask, request, jsonify, Response

from backend.processor import JobProcessor
from backend.data_model.requests import SimulationRequest
from backend.data_model.responses import SimulationResponse


app = Flask(__name__)


async def generate(payload: SimulationRequest):
    for i in range(payload.duration):
        response: SimulationResponse = await JobProcessor.process_job(payload.serialized, streaming=True)
        yield json.dumps(response.serialized) + "\n"
        time.sleep(1)


@app.route('/simulate', methods=['POST'])
async def simulate():
    # validate request by fitting it into the datamodel 
    payload = SimulationRequest(**request.get_json())

    # run the simulation:
    # response: SimulationResponse = await JobProcessor.process_job(payload.serialized)
    # return jsonify(response.serialized)
    return Response(generate(payload), mimetype="application/json")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

# worker/main.py
from concurrent import futures
import grpc
import time
import json
import simulation_pb2
import simulation_pb2_grpc
from google.protobuf.struct_pb2 import Struct

from process_bigraph import ProcessTypes
from vivarium import Vivarium
from bsp import app_registrar


class JobProcessor(object):
    @classmethod
    def run_interval(cls, viv: Vivarium) -> dict:
        """Runs a vivarium simulation for an atomic interval index whose range spans a given job's duration"""
        if 'emitter' not in viv.get_state().keys():
            viv.add_emitter()

        viv.run(1)
        results = viv.get_results()
        return results.pop() if isinstance(results, list) else results  # type: ignore


class SimulationService(simulation_pb2_grpc.SimulatorServicer):
    def SubmitSimulation(self, request, context):
        document = json.loads(request.document.ToJsonString())
        viv = Vivarium(...)  # create from document
        for i in range(request.duration):
            results = JobProcessor.run_interval(viv)
            yield simulation_pb2.SimulationResponse(
                job_id=request.job_id,
                timestamp=request.timestamp,
                status=f"STREAMING:{i}",
                results=to_struct(results),
                interval_id=i,
            )
            time.sleep(0.5)


def to_struct(d: dict) -> Struct:
    struct = Struct()
    struct.update(d)
    return struct

def get_core(source=None) -> ProcessTypes:   
    return app_registrar.core if not source else source


def new_vivarium(document):
    core = get_core()
    return Vivarium(
        processes=core.process_registry.registry,
        types=core.types(),
        core=core,
        document=document
    )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    simulation_pb2_grpc.add_SimulatorServicer_to_server(SimulationService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("🚀 Python Worker running on :50051")
    server.wait_for_termination()

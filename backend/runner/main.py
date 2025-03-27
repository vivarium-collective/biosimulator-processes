# worker/main.py
from concurrent import futures
import sys
import grpc
import time
import json
from google.protobuf.struct_pb2 import Struct

from process_bigraph import ProcessTypes
from vivarium import Vivarium
from backend.runner import runner_pb2, runner_pb2_grpc
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


def get_core(source=None) -> ProcessTypes:
    return app_registrar.core if not source else source


def new_vivarium(document):
    core = get_core()
    return Vivarium(
        processes=core.process_registry.registry,
        types=core.types(),
        core=core,
        document=document,
    )


def to_struct(d: dict) -> Struct:
    struct = Struct()
    struct.update(d)
    return struct


class SimulationRunner(runner_pb2_grpc.SimulationRunnerServicer):
    def RunSimulation(self, request_iterator, context):
        for job in request_iterator:
            print(f"Python Runner: Received job {job.job_id}")
            viv = new_vivarium(job.document)

            for i in range(job.duration):
                result = JobProcessor.run_interval(viv)
                yield runner_pb2.SimulationResult(
                    job_id=job.job_id,
                    interval_id=i,
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    status="running",
                    results=json.dumps(result),
                )
                time.sleep(1)  # simulate real time

            print(f"Python Runner: Completed job {job.job_id}")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    runner_pb2_grpc.add_SimulationRunnerServicer_to_server(SimulationRunner(), server)
    server.add_insecure_port('[::]:6000')
    print("Python Runner listening on :6000")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
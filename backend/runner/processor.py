import logging
import os
import json 
from typing import Any, Mapping

from dotenv import load_dotenv
from vivarium import Vivarium
from process_bigraph import ProcessTypes

from bsp import app_registrar

# from backend.runner.db import MongoConnector
from backend.runner.data_model.responses import IntervalResponse
from backend.runner.handlers import timestamp


class JobProcessor(object):
    @classmethod
    def run_interval(cls, viv: Vivarium) -> dict:
        print(f'Runner Got request document:\n{viv.make_document()}\n\n')
        """Runs a vivarium simulation for an atomic interval index whose range spans a given job's duration"""
        if 'emitter' not in viv.get_state().keys():
            viv.add_emitter()

        viv.run(1)
        results = viv.get_results()
        print(f'Runner.Processor got result: {results}\n')
        return results.pop() if isinstance(results, list) else results  # type: ignore
            

def test_job_processor():
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

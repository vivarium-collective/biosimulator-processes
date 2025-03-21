import logging
from typing import Any, Mapping

from dotenv import load_dotenv
from vivarium import Vivarium

from bsp import app_registrar

from backend.db import MongoConnector
from backend.data_model.responses import SimulationResponse
from backend.handlers import timestamp


core = app_registrar.core


class JobProcessor(object):
    @classmethod
    def process_request(cls, spec: dict, duration: int) -> list[dict[str, Any]]:
        """Runs a Vivarium simulation and returns results."""
        viv = Vivarium(
            processes=core.process_registry.registry,
            types=core.types(),
            core=core,
            document={'state': spec}
        )
        if 'emitter' not in viv.get_state().keys():
            viv.add_emitter()

        viv.run(duration)
        return viv.get_results()

    @classmethod
    async def process_job(cls, job: Mapping[str, Any], streaming: bool = True) -> SimulationResponse:
        """Processes a single job asynchronously."""
        job_id = job['job_id']
        status = job['status']
        if status.lower() != 'pending':
            return

        logging.info(f"Processing job {job_id}...")

        try:
            # await conn.update_job(job_id=job_id, status='IN_PROGRESS')
            request_spec = job.get('spec')
            duration = 1 if streaming else job.get('duration', 10)
            result = cls.process_request(spec=request_spec, duration=duration)

            # await conn.write(
            #     collection_name='results',
            #     job_id=job_id,
            #     result=result,
            #     last_updated=str(datetime.datetime.now()),
            #     status='COMPLETE'
            # )

            logging.info(f"Job {job_id} completed.")

            return SimulationResponse(
                job_id=job_id,
                last_updated=timestamp(),
                status="COMPLETE",
                results=result
            )

        except Exception as e:
            ##await conn.update_job(job_id=job_id, status='FAILED')
            logging.error(f"Error processing job {job_id}: {e}") 
            


import datetime
import os
from asyncio import run as asyncio_run, sleep
from typing import Any, Mapping

from dotenv import load_dotenv
from vivarium import Vivarium

from bsp import app_registrar
from bsp.server.db import MongoConnector


load_dotenv()

conn = MongoConnector(connection_uri=os.getenv("MONGO_URI"), database_id=os.getenv("DB_NAME"))
core = app_registrar.core


def process_request(spec: dict, duration: int) -> list[dict[str, Any]]:
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


async def run(timeout: int = 5, max_timeout: int = 20, buffer: float = 0.5):
    running = True
    while running:
        jobs: list[Mapping[str, Any]] = conn.get_jobs()
        if len(jobs):
            for job in jobs:
                job_id = job['job_id']
                status = job['status']
                if status.lower() == 'pending':
                    await conn.update_job(job_id=job_id, status='IN_PROGRESS')

                    request_spec = job.get('spec')
                    result = process_request(spec=request_spec, duration=job.get('duration', 10))

                    await conn.write(
                        collection_name='results',
                        job_id=job_id,
                        result=result,
                        last_updated=str(datetime.datetime.now()),
                        status='COMPLETE'
                    )
                    await sleep(buffer)


if __name__ == '__main__':
    asyncio_run(run())


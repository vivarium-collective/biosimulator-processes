import asyncio
import datetime
import os
import logging
from typing import Any, Mapping
from dotenv import load_dotenv
from vivarium import Vivarium
from bsp import app_registrar
from backend.db import MongoConnector

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Mongo connection
conn = MongoConnector(
    connection_uri=os.getenv("MONGO_URI"), 
    database_id=os.getenv("DB_NAME")
)
core = app_registrar.core

POLL_INTERVAL = 5  # Fallback polling interval (if change stream fails)
MAX_CONCURRENT_JOBS = 5


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
    async def process_job(cls, job: Mapping[str, Any]):
        """Processes a single job asynchronously."""
        job_id = job['job_id']
        status = job['status']

        if status.lower() != 'pending':
            return

        logging.info(f"Processing job {job_id}...")

        try:
            await conn.update_job(job_id=job_id, status='IN_PROGRESS')
            request_spec = job.get('spec')
            duration = job.get('duration', 10)

            result = cls.process_request(spec=request_spec, duration=duration)

            await conn.write(
                collection_name='results',
                job_id=job_id,
                result=result,
                last_updated=str(datetime.datetime.now()),
                status='COMPLETE'
            )

            logging.info(f"Job {job_id} completed.")

        except Exception as e:
            logging.error(f"Error processing job {job_id}: {e}")
            await conn.update_job(job_id=job_id, status='FAILED')


class JobDispatcher(object):
    processor: JobProcessor

    def __init__(self, connection_uri: str | None = None, conn: MongoConnector | None = None, **params):
        self.conn = conn or MongoConnector(connection_uri=connection_uri, database_id="bsp")
        if params:
            for k, v in params.items():
                setattr(self, k, v)

    async def listen(self):
        logging.info("Listening for new jobs...")
        try:
            with self.conn.db.watch([{"$match": {"operationType": "insert"}}]) as stream:
                for change in stream:
                    job = change["fullDocument"]
                    asyncio.create_task(
                        self.processor.process_job(job)
                    )
        except Exception as e:
            logging.error(f"Change Stream failed: {e}")
            logging.info("Switching to fallback polling...")
            await self.fallback()

    async def fallback(self, buffer: int = 5):
        wait_time = buffer
        while True:
            jobs = await self.conn.get_jobs()
            if jobs:
                await asyncio.gather(*[self.processor.process_job(job) for job in jobs])
                wait_time = buffer
            else:
                # exp backoff TODO: optimize this prior to prod
                wait_time = min(wait_time * 2, 60)
            await asyncio.sleep(wait_time)

    async def run(self):
        """Runs both Change Streams and fallback polling."""
        await asyncio.gather(self.listen(), self.fallback())


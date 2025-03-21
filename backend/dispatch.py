import asyncio
import datetime
import os
import logging
from typing import Any, Mapping

from dotenv import load_dotenv
from vivarium import Vivarium

from bsp import app_registrar

from backend.db import MongoConnector
from backend.data_model.responses import SimulationResponse
from backend.handlers import timestamp


load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Mongo connection
# conn = MongoConnector(
#     connection_uri=os.getenv("MONGO_URI"), 
#     database_id=os.getenv("DB_NAME")
# )
core = app_registrar.core

POLL_INTERVAL = 5  # Fallback polling interval (if change stream fails)
MAX_CONCURRENT_JOBS = 5


class JobDispatcher(object):
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


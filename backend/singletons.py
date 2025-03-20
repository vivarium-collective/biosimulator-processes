import logging
import os

from dotenv import load_dotenv

from backend.db import MongoConnector


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

mongo_conn = MongoConnector(connection_uri=MONGO_URI, connector_id="backend.singletons.mongo_conn")


def stream_listener():
    with mongo_conn.db.simulations.watch() as stream:
        for change in stream:
            print(f'Detected a stream change in the simulations collection: {change}')



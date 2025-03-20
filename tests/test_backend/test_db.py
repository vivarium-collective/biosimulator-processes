import os
from datetime import datetime

import pymongo
import pytest
from dotenv import load_dotenv


load_dotenv()


@pytest.fixture
def test_entry():
    return {
        "job_id": "test_job",
        "last_updated": datetime.now(),
        "spec": {
            "membrane": {
                "address": "local:simple-membrane-process"
            }
        }
    }


@pytest.mark.usefixtures("test_entry")
def test_db_entry(test_entry):
    client: pymongo.MongoClient = pymongo.MongoClient(os.environ['MONGO_URI_ALT'])
    confirmation = client.changestream.collection.insert_one(test_entry)
    print(f'{__name__} confirmation ID: {confirmation.inserted_id}')


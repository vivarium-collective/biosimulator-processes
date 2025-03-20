import json
import os
import pymongo
from bson.json_util import dumps
from dotenv import load_dotenv


load_dotenv()

client = pymongo.MongoClient(os.environ['MONGO_URI_ALT'])
with client.db.watch([{"$match": {"operationType": "insert"}}]) as stream:
    for change in stream:
        job = change["fullDocument"]
        print(
            'Got job',
            json.dumps(job)
        )
        # asyncio.create_task(
        #     self.processor.process_job(job)
        # )


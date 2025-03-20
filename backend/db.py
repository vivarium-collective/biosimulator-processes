from abc import abstractmethod, ABC
from typing import *

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import UpdateResult

from backend.handlers import timestamp


class DatabaseConnector(ABC):
    database_id: str
    local: bool
    client: Any
    db: Any
    connection_uri: str
    connector_id: Optional[str]
    _default_job_collection_id: str = 'simulations'

    def __init__(
            self,
            connection_uri: str | None = None,
            database_id: str | None = "bsp",
            connector_id: str | None = None,
            local: bool = False,
            job_collection_id: str = _default_job_collection_id,
    ):
        self.database_id = database_id
        self.local = local
        self.client = self._get_client(connection_uri)
        self.db = self._get_database(self.database_id)
        self.connector_id = connector_id or "unnamed_database_connector"
        self.connection_uri = connection_uri
        self._default_job_collection_id = job_collection_id

    @abstractmethod
    def _get_client(self, *args):
        pass

    @abstractmethod
    def _get_database(self, db_id: str):
        pass

    @abstractmethod
    async def read(self, collection_name: str, *args, **kwargs):
        pass

    @abstractmethod
    async def write(self, collection_name: str, *args, **kwargs):
        pass

    @property
    @abstractmethod
    def storage(self):
        pass

    @property
    @abstractmethod
    def job_collection(self):
        pass

    @abstractmethod
    async def update_job_status(self, job_id: str, status: str):
        pass

    @abstractmethod
    async def get_jobs(self):
        pass

    @abstractmethod
    def refresh_jobs(self):
        pass


class MongoConnector(DatabaseConnector):
    def __init__(self,
                 connection_uri: str | None = None,
                 database_id: str | None = None,
                 connector_id: str | None = None,
                 local: bool = False,
                 all_ports: bool = False):
        host: str = "0.0.0.0" if all_ports else "mongodb"
        self._default_connection_uri: str = f"mongodb://{host}:27017/?replicaSet=rs0"
        connection_uri = connection_uri or self._default_connection_uri
        super().__init__(connection_uri, database_id, connector_id, local)

    def _get_client(self, *args):
        return MongoClient(args[0]) if not self.local else MongoClient("localhost", 27017)

    def _get_database(self, db_id: str) -> Database:
        return self.client.get_database(db_id)

    def get_collection(self, collection_name: str) -> Collection:
        return self.db[collection_name]

    @property
    def storage(self):
        return {coll_name: [v for v in self.db[coll_name].find()] for coll_name in self.db.list_collection_names()}

    async def read(self, collection_name: str, **kwargs):
        coll = self.get_collection(collection_name)
        result = coll.find_one(kwargs.copy())
        return result

    async def write(self, collection_name: str, **kwargs):
        try:
            coll = self.get_collection(collection_name)
            result = coll.insert_one(kwargs.copy())
            return kwargs.copy()
        except:
            raise IOError(f"Failed to insert: {kwargs} into {collection_name}. Check your inputs.")

    @property
    def job_collection(self) -> Collection:
        return self.get_collection(self._default_job_collection_id)

    @property
    def results_collection(self) -> Collection:
        return self.get_collection("results")

    async def get_jobs(self):
        return self.jobs

    @property
    def jobs(self):
        return [item for item in self.job_collection.find()]

    async def update_job(self, job_id: str, **updates) -> UpdateResult:
        return self.job_collection.update_one(
            filter={'job_id': job_id},
            update={
                '$set': {**updates}
            }
        )

    async def update_job_status(self, job_id: str, status: str) -> UpdateResult:
        result = await self.update_job(job_id, status=status, last_updated=timestamp())
        return result

    def refresh_jobs(self):
        coll = self._default_job_collection_id
        for job in self.db[coll].find():
            self.db[coll].delete_one(job)


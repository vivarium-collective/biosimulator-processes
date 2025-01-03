import os
import re
import uuid
from abc import abstractmethod
from logging import warn
from uuid import uuid4
from typing import *

from process_bigraph.composite import Emitter, Process
from pymongo import ASCENDING, MongoClient
from pymongo.database import Database


HISTORY_INDEXES = [
    'data.time',
    [('experiment_id', ASCENDING),
     ('data.time', ASCENDING),
     ('_id', ASCENDING)],
]
CONFIGURATION_INDEXES = [
    'experiment_id',
]
SECRETS_PATH = 'secrets.json'


# -- emitters -- #

DB_CONFIG_TYPE = {
    'connection_uri': 'string',
    'experiment_id': 'maybe[string]',
    'emit_limit': 'integer',
    'database': 'maybe[string]',
}


class DatabaseEmitter(Emitter):
    config_schema = {
        'connection_uri': 'string',
        'experiment_id': 'maybe[string]',
        'emit_limit': 'integer',
        'database': 'maybe[string]',
    }

    @abstractmethod
    def create_indexes(self, table: Any, columns: List[Any]) -> None:
        pass

    @property
    def current_pid(self):
        return os.getpid()

    def __init__(self, config=None, core=None):
        """Config may have 'host' and 'database' items. The config passed is expected to be:

                {'experiment_id':,
                 'emit_limit':,
                 'embed_path':}

                TODO: Automate this process for the user in builder
        """
        super().__init__(config, core)
        # self.core = core
        self.experiment_id = self.config.get('experiment_id', str(uuid.uuid4()))
        self.emit_limit = self.config.get('emit_limit', 4000000)


class MongoDatabaseEmitter(DatabaseEmitter):
    client_dict: Dict[int, MongoClient] = {}
    config_schema = {
        'connection_uri': 'string',
        'experiment_id': 'maybe[string]',
        'emit_limit': {
            '_type': 'integer',
            '_default': 4000000
        },
        'database': 'maybe[string]'
    }

    @classmethod
    def create_indexes(cls, table: Any, columns: List[Any]) -> None:
        """Create the listed column indexes for the given DB table."""
        for column in columns:
            table.create_index(column)

    def __init__(self, config, core) -> None:
        """Config may have 'host' and 'database' items. The config passed is expected to be:

                {'experiment_id':,
                 'emit_limit':,
                 'embed_path':}

                TODO: Automate this process for the user in builder
        """
        super().__init__(config)
        self.core = core
        self.experiment_id = self.config.get('experiment_id', str(uuid.uuid4()))
        # In the worst case, `breakdown_data` can underestimate the size of
        # data by a factor of 4: len(str(0)) == 1 but 0 is a 4-byte int.
        # Use 4 MB as the breakdown limit to stay under MongoDB's 16 MB limit.
        self.emit_limit = self.config['emit_limit']

        # create new MongoClient per OS process
        curr_pid = os.getpid()
        if curr_pid not in MongoDatabaseEmitter.client_dict:
            MongoDatabaseEmitter.client_dict[curr_pid] = MongoClient(
                config['connection_uri'])
        self.client: MongoClient = MongoDatabaseEmitter.client_dict[curr_pid]

        # extract objects from current mongo client instance
        self.db: Database = getattr(self.client, self.config.get('database', 'simulations'))
        self.history_collection: Collection = getattr(self.db, 'history')
        self.configuration: Collection = getattr(self.db, 'configuration')

        # create column indexes for the given collection objects
        self.create_indexes(self.history_collection, HISTORY_INDEXES)
        self.create_indexes(self.configuration, CONFIGURATION_INDEXES)

        self.fallback_serializer = make_fallback_serializer_function(self.core)

    def query(self, query):
        return self.history_collection.find_one(query)

    def history(self):
        return [v for v in self.history_collection.find()]

    def flush_history(self):
        for v in self.history():
            self.history_collection.delete_one(v)

    def update(self, inputs):
        self.history_collection.insert_one(inputs)
        return {}


def make_fallback_serializer_function(process_registry) -> Callable:
    """Creates a fallback function that is called by orjson on data of
    types that are not natively supported. Define and register instances of
    :py:class:`vivarium.core.registry.Serializer()` with serialization
    routines for the types in question."""

    def default(obj: Any) -> Any:
        # Try to lookup by exclusive type
        serializer = process_registry.access(str(type(obj)))
        if not serializer:
            compatible_serializers = []
            for serializer_name in process_registry.list():
                test_serializer = process_registry.access(serializer_name)
                # Subclasses with registered serializers will be caught here
                if isinstance(obj, test_serializer.python_type):
                    compatible_serializers.append(test_serializer)
            if len(compatible_serializers) > 1:
                raise TypeError(
                    f'Multiple serializers ({compatible_serializers}) found '
                    f'for {obj} of type {type(obj)}')
            if not compatible_serializers:
                raise TypeError(
                    f'No serializer found for {obj} of type {type(obj)}')
            serializer = compatible_serializers[0]
            if not isinstance(obj, Process):
                # We don't warn for processes because since their types
                # based on their subclasses, it's not possible to avoid
                # searching through the serializers.
                warn(
                    f'Searched through serializers to find {serializer} '
                    f'for data of type {type(obj)}. This is '
                    f'inefficient.')
        return serializer.serialize(obj)

    return default

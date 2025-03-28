import abc
from typing import Any


class ConnectionManager(abc.ABC):
    @property
    @abc.abstractmethod
    def active_connections(self) -> dict:
        pass
    
    @abc.abstractmethod
    async def connect(self, client_id: str, connection: Any):
        pass

    @abc.abstractmethod
    def disconnect(self, connection: Any):
        pass

    @abc.abstractmethod
    async def send_to(self, client_id: str, connection: Any, message: dict):
        pass

    async def broadcast(self, message: dict):
        for id, connection in self.active_connections.items():
            await self.send_to(id, connection, message)
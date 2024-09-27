from abc import ABC, abstractmethod
from DataBase.MongoHandler import MongoDBHandler
from DataBase.MySQLHandler import MySQLHandler

class Database(ABC):
    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def save_settings(self, settings: dict):
        pass

def get_database_handler(db_type: str) -> Database:
    if db_type == "MONGO":
        return MongoDBHandler()
    elif db_type == "MYSQL":
        return MySQLHandler()
    else:
        raise ValueError("Unsupported database type")

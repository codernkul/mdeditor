import os

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "mdeditor")

_client: Optional[AsyncIOMotorClient] = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URI)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    """Return the application database (dependency-injectable for tests)."""
    return get_client()[MONGO_DB]


def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None

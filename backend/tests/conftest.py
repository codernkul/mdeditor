import asyncio
import os

from motor.motor_asyncio import AsyncIOMotorClient

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ["MONGO_DB"] = "mdeditor_test"

from app.database import close_client, get_client  # noqa: E402
from app.main import app  # noqa: E402

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    """Give every test a fresh, empty test database (before and after).

    Uses its own short-lived client so it never touches a Motor client
    bound to a previous test's (closed) event loop.
    """
    client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["mdeditor_test"]
    await db.documents.delete_many({})
    yield db
    await db.documents.delete_many({})
    client.close()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Run startup handlers (indexes + seeding) manually since ASGITransport
        # bypasses the ASGI lifespan stack.
        for handler in app.router.on_startup:
            await handler()
        # Startup seeds a sample doc; clear so tests start from a clean slate.
        await get_client()["mdeditor_test"].documents.delete_many({})
        yield ac
    close_client()


def teardown_module(module):
    # Drop the test database with a fresh client (any cached client may be
    # bound to a closed loop by the time module teardown runs).
    one_shot = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    one_shot.drop_database("mdeditor_test")
    one_shot.close()
    close_client()

import logging

from typing import List

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from .database import close_client, get_db
from .models import DocumentCreate, DocumentOut, DocumentSummary, DocumentUpdate, utcnow

logger = logging.getLogger("uvicorn.error")

SAMPLE_DOC = """# Welcome to mdeditor 👋

This is a **sample document** stored in MongoDB. Edit the markdown on the
left and watch the rich preview update on the right.

## Features

- Full CRUD for `.md` documents (create, read, update, delete)
- Import an existing `.md` file from your computer
- Live rich-text preview with GitHub-flavored markdown support
- Everything persisted in MongoDB

## Markdown cheatsheet

| Feature | Syntax |
| ------- | ------ |
| Bold | `**bold**` |
| Italic | `*italic*` |
| Code | `` `code` `` |
| Link | `[text](https://example.com)` |

> Blockquotes, lists, tables, and more are all supported.

1. Edit the text on the left
2. Click **Save**
3. Reload the page — your changes persist
"""

app = FastAPI(
    title="mdeditor API",
    description="Full CRUD REST API for markdown documents (FARM stack)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3010", "http://127.0.0.1:3010"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """Idempotently create indexes (unique doc names, sorted list queries)."""
    await db.documents.create_index("name", unique=True)
    await db.documents.create_index([("updated_at", -1)])


@app.on_event("startup")
async def startup() -> None:
    db = get_db()
    await ensure_indexes(db)
    if await db.documents.count_documents({}) == 0:
        now = utcnow()
        await db.documents.insert_one(
            {
                "name": "welcome.md",
                "content": SAMPLE_DOC,
                "created_at": now,
                "updated_at": now,
            }
        )
        logger.info("Seeded database with sample document 'welcome.md'")


@app.on_event("shutdown")
async def shutdown() -> None:
    close_client()


def to_summary(doc: dict) -> dict:
    content = doc.get("content", "")
    return {
        "_id": str(doc["_id"]),
        "name": doc["name"],
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
        "chars": len(content),
        "words": len(content.split()),
    }


def to_out(doc: dict) -> dict:
    return {
        "_id": str(doc["_id"]),
        "name": doc["name"],
        "content": doc["content"],
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }


async def fetch_doc(db: AsyncIOMotorDatabase, doc_id: str) -> dict:
    try:
        oid = ObjectId(doc_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=404, detail="Document not found")
    doc = await db.documents.find_one({"_id": oid})
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/documents", response_model=List[DocumentSummary])
async def list_documents(db: AsyncIOMotorDatabase = Depends(get_db)):
    cursor = db.documents.find().sort("updated_at", -1)
    docs = []
    async for doc in cursor:
        docs.append(to_summary(doc))
    return docs


@app.post(
    "/api/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    payload: DocumentCreate, db: AsyncIOMotorDatabase = Depends(get_db)
):
    now = utcnow()
    document = {
        "name": payload.name,
        "content": payload.content,
        "created_at": now,
        "updated_at": now,
    }
    try:
        result = await db.documents.insert_one(document)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409, detail=f"A document named '{payload.name}' already exists"
        )
    created = await db.documents.find_one({"_id": result.inserted_id})
    return to_out(created)


@app.get("/api/documents/{doc_id}", response_model=DocumentOut)
async def get_document(doc_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await fetch_doc(db, doc_id)
    return to_out(doc)


@app.put("/api/documents/{doc_id}", response_model=DocumentOut)
async def update_document(
    doc_id: str,
    payload: DocumentUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await fetch_doc(db, doc_id)

    updates = {}
    if payload.name is not None and payload.name != doc["name"]:
        updates["name"] = payload.name
    if payload.content is not None and payload.content != doc["content"]:
        updates["content"] = payload.content
    if not updates:
        return to_out(doc)  # nothing changed

    updates["updated_at"] = utcnow()
    try:
        await db.documents.update_one({"_id": doc["_id"]}, {"$set": updates})
    except DuplicateKeyError:
        detail = "Update conflicts with an existing document"
        if payload.name:
            detail = f"A document named '{payload.name}' already exists"
        raise HTTPException(status_code=409, detail=detail)
    updated = await db.documents.find_one({"_id": doc["_id"]})
    return to_out(updated)


@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await fetch_doc(db, doc_id)
    await db.documents.delete_one({"_id": doc["_id"]})
    return JSONResponse({"deleted": True, "id": doc_id, "name": doc["name"]})

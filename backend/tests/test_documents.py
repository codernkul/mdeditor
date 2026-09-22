"""Integration tests for the mdeditor CRUD API (uses real local MongoDB)."""
import pytest

pytestmark = pytest.mark.asyncio


DOC = {"name": "notes.md", "content": "# Notes\n\nHello **world**"}


async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_create_and_get_document(client):
    resp = await client.post("/api/documents", json=DOC)
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "notes.md"
    assert body["content"] == DOC["content"]
    assert body["id"]

    got = await client.get(f"/api/documents/{body['id']}")
    assert got.status_code == 200
    assert got.json()["content"] == DOC["content"]


async def test_create_appends_md_extension(client):
    resp = await client.post("/api/documents", json={"name": "readme", "content": "x"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "readme.md"


async def test_create_rejects_blank_name(client):
    resp = await client.post("/api/documents", json={"name": "   ", "content": "x"})
    assert resp.status_code == 422


async def test_create_duplicate_name_conflicts(client):
    assert (await client.post("/api/documents", json=DOC)).status_code == 201
    resp = await client.post("/api/documents", json={"name": "notes.md", "content": "other"})
    assert resp.status_code == 409


async def test_list_documents(client):
    await client.post("/api/documents", json=DOC)
    await client.post("/api/documents", json={"name": "second.md", "content": "two words here"})
    resp = await client.get("/api/documents")
    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) == 2
    summary = next(d for d in docs if d["name"] == "second.md")
    assert summary["words"] == 3
    assert summary["chars"] == len("two words here")
    assert "content" not in summary  # summaries exclude the body


async def test_update_document(client):
    doc_id = (await client.post("/api/documents", json=DOC)).json()["id"]
    resp = await client.put(f"/api/documents/{doc_id}", json={"content": "# Updated"})
    assert resp.status_code == 200
    assert resp.json()["content"] == "# Updated"

    got = await client.get(f"/api/documents/{doc_id}")
    assert got.json()["content"] == "# Updated"


async def test_rename_document(client):
    doc_id = (await client.post("/api/documents", json=DOC)).json()["id"]
    resp = await client.put(f"/api/documents/{doc_id}", json={"name": "renamed.md"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "renamed.md"


async def test_rename_to_existing_name_conflicts(client):
    await client.post("/api/documents", json=DOC)
    other_id = (
        await client.post("/api/documents", json={"name": "other.md", "content": "y"})
    ).json()["id"]
    resp = await client.put(f"/api/documents/{other_id}", json={"name": "notes.md"})
    assert resp.status_code == 409


async def test_update_noop_keeps_timestamp(client):
    doc_id = (await client.post("/api/documents", json=DOC)).json()
    before = doc_id["updated_at"]
    resp = await client.put(f"/api/documents/{doc_id['id']}", json={"content": DOC["content"]})
    assert resp.status_code == 200
    assert resp.json()["updated_at"] == before


async def test_delete_document(client):
    doc_id = (await client.post("/api/documents", json=DOC)).json()["id"]
    resp = await client.delete(f"/api/documents/{doc_id}")
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True
    assert (await client.get(f"/api/documents/{doc_id}")).status_code == 404


async def test_get_unknown_and_malformed_ids(client):
    assert (await client.get("/api/documents/000000000000000000000000")).status_code == 404
    assert (await client.get("/api/documents/not-an-objectid")).status_code == 404

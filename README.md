# mdeditor — a FARM-stack markdown editor

A markdown editor built with the **FARM** stack: **F**astAPI, **R**eact, **M**ongoDB.

- **Left pane** — plain-text markdown editor (with live line/word/char counts)
- **Right pane** — rich rendered preview (GitHub-flavored markdown via `react-markdown` + `remark-gfm`)
- Full CRUD for markdown documents stored in MongoDB, plus import of an existing `.md` file from disk

## Features

| Action | How |
| ------ | --- |
| Create | `＋ New` button → edit → `💾 Save` (also `Ctrl/Cmd+S`) |
| Read   | Pick a document from the dropdown; preview renders on the right |
| Update | Edit the text and `💾 Save` |
| Delete | `🗑 Delete` (with confirmation) |
| Import | `⬆ Import .md` loads any local `.md` file into the editor; `Save` persists it to MongoDB |

Duplicate document names are rejected (unique index) and the app surfaces a friendly conflict message.

## Project layout

```
backend/            FastAPI + Motor (async MongoDB driver)
├── app/
│   ├── main.py     REST API: GET/POST/PUT/DELETE /api/documents
│   ├── models.py   Pydantic request/response models
│   └── database.py Mongo connection management
├── tests/          pytest integration tests (12) against a real MongoDB test DB
└── requirements.txt

frontend/           Vite + React SPA
└── src/
    ├── App.jsx     Split-pane editor + live preview UI
    └── api.js      Typed fetch wrappers for the REST API
```

## Running it

Prerequisites: Python 3.8+, Node 18+, and a local MongoDB on `mongodb://localhost:27017`.

**1. Backend** (port 8010 — port 8000 is commonly taken by other apps):

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r tests/requirements.txt
.venv/bin/uvicorn app.main:app --reload --port 8010
```

On first start the API seeds a sample `welcome.md` document.
Environment overrides: `MONGO_URI`, `MONGO_DB` (defaults: `mongodb://localhost:27017`, `mdeditor`).

**2. Frontend** (port 3010, proxies `/api` → `http://localhost:8010`):

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:3010.

## Tests

```bash
cd backend
.venv/bin/python -m pytest tests -q
```

The suite uses a dedicated `mdeditor_test` database (created and dropped automatically), so your real data is untouched.

## API reference

Interactive docs at http://localhost:8010/docs.

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET    | `/api/health` | Liveness check |
| GET    | `/api/documents` | List documents (summaries, newest first) |
| POST   | `/api/documents` | Create `{ "name": "notes.md", "content": "# …" }` |
| GET    | `/api/documents/{id}` | Fetch one document |
| PUT    | `/api/documents/{id}` | Update name and/or content |
| DELETE | `/api/documents/{id}` | Delete a document |

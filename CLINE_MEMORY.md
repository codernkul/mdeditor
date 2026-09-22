# mdeditor — Context Memory

_Last updated: 2026-09-22 (after fixing the vertical-split pane layout bug)._

## Goal
FARM-stack (FastAPI + React + MongoDB) markdown editor webapp with split-pane editor (left) and rich-text rendered preview (right), full CRUD, plus import of existing `.md` files. Optional future: in-app AI/LLM agent panel (offered, user has not decided).

## Current State — Done
- **Backend:** Full CRUD API (FastAPI + Motor) at `backend/app/` — 12 pytest integration tests passing.
- **Frontend:** Vite + React (`react-markdown` + `remark-gfm`). Toolbar (New / Import / Save / Delete), doc dropdown, dirty badge, word/line/char counts, live split-pane preview.
- **Blank-browser bug fixed:** `openDoc(docId)` fetches full doc via `GET /api/documents/{id}` (list summaries lack `content`).
- **Corrupted `App.css` fixed** (root cause of an earlier "stuck single-view" report): rewritten cleanly (~340 lines) — fixed toolbar, 2-pane grid, independently scrollable editor (`textarea`) and preview (`overflow-y: auto`), dark theme + markdown-body styles, responsive stack below 900px.
- **Draggable pane resizer:** `editorSize` state in `App.jsx` (default 50%), `panesRef` on `.panes`, `startResize` pointer-drag clamped 15%–85%, double-click resets to 50/50; `body.resizing` class prevents text selection.
- **Pane-layout bug FIXED (latest):** `.panes` grid declared only 2 columns (`var(--editor-size) 1fr`) but has **3 children** (editor, resizer, preview). The resizer consumed the `1fr` column (big empty right area) and the preview wrapped onto an implicit 2nd row — looked like editor/preview stacked vertically with empty right side.
  - Fix in `App.css`: `grid-template-columns: var(--editor-size, 50%) 6px minmax(0, 1fr)` (resizer gets its own 6px track). Mobile media query: `grid-template-rows: var(--editor-size, 50%) 6px minmax(0, 1fr)` with single column.
  - Fix in `App.jsx`: `startResize` now checks `matchMedia('(max-width: 900px)')` and uses `clientY`/`rect.height` for the stacked (row-handle) mode; X-axis logic unchanged for desktop.
  - Verified: `npm run build` passes; headless Chrome screenshot of :3010 confirms editor | 6px resizer | preview side-by-side, top-aligned, independently scrollable.

## Environment / Gotchas
- **Ports:** frontend **:3010**, backend **:8010** (8000 taken by unrelated Docker app); Vite proxy `/api` → 8010; CORS allows 3010. Both servers left running; logs at `/tmp/mdeditor_backend.log`, `/tmp/mdeditor_frontend.log`.
- **Python 3.8** → pins `uvicorn==0.30.6`, `pytest-asyncio==0.24.0`; venv at `backend/.venv` (system site-packages not writable); **avoid `list[...]` generics**.
- **Pydantic v2** uses `validation_alias="_id"` so API returns `id`; test fixtures use fresh Motor client per fixture (avoids closed-event-loop errors).
- **Editing files:** large tool calls must be split (<6000 chars); prefer the editor tool over shell heredocs for JSX/CSS — a heredoc corrupted `App.css`/`App.jsx` before.
- **Verification tooling:** no puppeteer installed; use headless Chrome directly:
  `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome --headless=new --screenshot=/tmp/x.png --window-size=1400,900 --virtual-time-budget=8000 http://localhost:3010` (ignore `task_policy_set` stderr noise), then read the PNG.
- User has a 62k-char imported doc (~834 lines); preview may need lazy/chunked rendering if sluggish (offered, not requested).

## Candidate Next Steps
1. Persist `editorSize` to `localStorage` across sessions (few lines, offered).
2. Lazy/chunked preview rendering for the large doc (offered).
3. In-app AI agent panel — CRUD foundation ready; awaiting user decision.

## Key Files
- Frontend: `frontend/src/App.jsx`, `frontend/src/App.css`, `frontend/src/index.css`, `frontend/src/api.js`, `frontend/vite.config.js`
- Backend: `backend/app/main.py`, `backend/app/models.py`, `backend/app/database.py`
- Tests: `backend/tests/conftest.py`, `backend/tests/test_documents.py`
- Docs: `README.md`

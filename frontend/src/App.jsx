import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  createDocument,
  deleteDocument,
  getDocument,
  listDocuments,
  updateDocument,
} from './api'
import './App.css'

export default function App() {
  const [docs, setDocs] = useState([])
  const [currentId, setCurrentId] = useState(null)
  const [name, setName] = useState('untitled.md')
  const [content, setContent] = useState('')
  const [savedContent, setSavedContent] = useState('')
  const [savedName, setSavedName] = useState('')
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const fileInputRef = useRef(null)
  const panesRef = useRef(null)
  const [editorSize, setEditorSize] = useState(50) // % width of the editor pane

  const dirty = content !== savedContent || name !== savedName

  // Drag the splitter between editor and preview.
  const startResize = (e) => {
    e.preventDefault()
    const rect = panesRef.current.getBoundingClientRect()
    // On narrow screens the panes stack vertically, so the handle moves rows.
    const isVertical =
      window.matchMedia('(max-width: 900px)').matches
    const onMove = (ev) => {
      const pct = isVertical
        ? ((ev.clientY - rect.top) / rect.height) * 100
        : ((ev.clientX - rect.left) / rect.width) * 100
      setEditorSize(Math.min(85, Math.max(15, pct)))
    }
    const onUp = () => {
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
      document.body.classList.remove('resizing')
    }
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
    document.body.classList.add('resizing')
  }

  const refreshDocs = useCallback(async () => {
    try {
      const list = await listDocuments()
      setDocs(list)
      return list
    } catch (err) {
      setError(`Could not load documents: ${err.message}`)
      return []
    }
  }, [])

  const openDoc = useCallback(async (docId) => {
    try {
      // Fetch the full document (the list endpoint only returns summaries).
      const doc = await getDocument(docId)
      setCurrentId(doc.id)
      setName(doc.name)
      setContent(doc.content ?? '')
      setSavedName(doc.name)
      setSavedContent(doc.content ?? '')
      setError('')
      setStatus(`Opened “${doc.name}”`)
    } catch (err) {
      setError(`Could not open document: ${err.message}`)
    }
  }, [])

  // Initial load: fetch the list and open the most recently edited doc.
  useEffect(() => {
    ;(async () => {
      const list = await refreshDocs()
      if (list.length > 0) openDoc(list[0].id)
    })()
  }, [refreshDocs, openDoc])

  const flash = (msg) => {
    setStatus(msg)
    setError('')
    window.clearTimeout(flash._t)
    flash._t = window.setTimeout(() => setStatus(''), 3000)
  }

  const newDoc = () => {
    setCurrentId(null)
    setName('untitled.md')
    setContent('')
    setSavedName('untitled.md')
    setSavedContent('')
    setError('')
    flash('New document ready — press Save to persist it')
  }

  const saveDoc = async () => {
    if (busy) return
    setBusy(true)
    try {
      if (currentId) {
        const updated = await updateDocument(currentId, { name, content })
        setSavedName(updated.name)
        setSavedContent(updated.content)
        setName(updated.name)
        flash(`Saved “${updated.name}”`)
      } else {
        const created = await createDocument(name, content)
        setCurrentId(created.id)
        setSavedName(created.name)
        setSavedContent(created.content)
        setName(created.name)
        flash(`Created “${created.name}”`)
      }
      await refreshDocs()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const removeDoc = async () => {
    if (!currentId) return
    if (!window.confirm(`Delete “${name}” permanently?`)) return
    setBusy(true)
    try {
      await deleteDocument(currentId)
      flash(`Deleted “${name}”`)
      setCurrentId(null)
      setName('untitled.md')
      setContent('')
      setSavedName('untitled.md')
      setSavedContent('')
      const list = await refreshDocs()
      if (list.length > 0) await openDoc(list[0].id)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  // Import an existing .md file from disk into the editor.
  const importFile = (event) => {
    const file = event.target.files && event.target.files[0]
    if (!file) return
    if (!/\.md$/i.test(file.name)) {
      setError('Please choose a .md file')
      event.target.value = ''
      return
    }
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = String(e.target.result)
      setCurrentId(null)
      setName(file.name)
      setContent(text)
      setSavedName(file.name)
      setSavedContent(text)
      setError('')
      flash(`Imported “${file.name}” — press Save to persist it in MongoDB`)
    }
    reader.readAsText(file)
    event.target.value = ''
  }

  // Ctrl/Cmd+S saves.
  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's') {
        e.preventDefault()
        saveDoc()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })


  const stats = useMemo(
    () => ({
      words: content.trim() ? content.trim().split(/\s+/).length : 0,
      chars: content.length,
      lines: content.split('\n').length,
    }),
    [content],
  )

  return (
    <div className="app">
      <header className="toolbar">
        <div className="brand">
          <span className="logo">M↓</span>
          <span>mdeditor</span>
        </div>

        <select
          className="doc-picker"
          value={currentId || ''}
          onChange={(e) => {
            if (e.target.value) openDoc(e.target.value)
          }}
        >
          <option value="" disabled>
            {docs.length ? 'Choose a document…' : 'No saved documents yet'}
          </option>
          {docs.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name} · {d.words} words
            </option>
          ))}
        </select>

        <div className="actions">
          <button onClick={newDoc} title="Start a new document">
            ＋ New
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            title="Import an existing .md file"
          >
            ⬆ Import .md
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".md,text/markdown"
            style={{ display: 'none' }}
            onChange={importFile}
          />
          <button
            className="primary"
            onClick={saveDoc}
            disabled={busy || !dirty}
            title="Save (Ctrl/Cmd+S)"
          >
            {busy ? 'Saving…' : dirty ? '💾 Save' : '✓ Saved'}
          </button>
          <button
            className="danger"
            onClick={removeDoc}
            disabled={busy || !currentId}
            title="Delete this document"
          >
            🗑 Delete
          </button>
        </div>
      </header>

      {(status || error) && (
        <div className={`notice ${error ? 'error' : 'info'}`}>
          {error || status}
        </div>
      )}

      <main
        className="panes"
        ref={panesRef}
        style={{ '--editor-size': `${editorSize}%` }}
      >
        <section className="pane editor-pane">
          <div className="pane-header">
            <input
              className="name-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              spellCheck={false}
              aria-label="Document name"
            />
            <span className={`badge ${dirty ? 'dirty' : 'clean'}`}>
              {dirty ? 'Unsaved changes' : 'In sync'}
            </span>
          </div>
          <textarea
            className="editor"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="# Start writing markdown here…"
            spellCheck={false}
          />
          <div className="pane-footer">
            {stats.lines} lines · {stats.words} words · {stats.chars} chars
          </div>
        </section>

        <div
          className="pane-resizer"
          role="separator"
          aria-orientation="vertical"
          title="Drag to resize panes · double-click to reset"
          onPointerDown={startResize}
          onDoubleClick={() => setEditorSize(50)}
        />

        <section className="pane preview-pane">
          <div className="pane-header">
            <span>Preview</span>
          </div>
          <div className="preview markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {content || '*Nothing to preview yet.*'}
            </ReactMarkdown>
          </div>
        </section>
      </main>
    </div>
  )
}

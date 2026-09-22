const API = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(body.detail || `Request failed (${res.status})`)
  }
  return body
}

export function listDocuments() {
  return request('/documents')
}

export function getDocument(id) {
  return request(`/documents/${id}`)
}

export function createDocument(name, content) {
  return request('/documents', {
    method: 'POST',
    body: JSON.stringify({ name, content }),
  })
}

export function updateDocument(id, { name, content }) {
  return request(`/documents/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ name, content }),
  })
}

export function deleteDocument(id) {
  return request(`/documents/${id}`, { method: 'DELETE' })
}

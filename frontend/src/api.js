// api.js — thin wrapper around the Flask backend
// In dev (Vite on localhost:5173) BASE is empty → Vite proxies /api/* to localhost:5000
// In production (Vercel) VITE_API_BASE_URL points at the Render backend
const BASE = import.meta.env.VITE_API_BASE_URL || ''

async function jsonFetch(url, opts = {}) {
  opts.credentials = 'include'
  const r = await fetch(url, opts)
  if (!r.ok) {
    let msg = `HTTP ${r.status}`
    try {
      const data = await r.json()
      msg = data.error || data.message || msg
    } catch { /* not JSON */ }
    throw new Error(msg)
  }
  return r.json()
}

export const api = {
  stats: () => jsonFetch(`${BASE}/api/stats`),
  logs: (since = 0) => jsonFetch(`${BASE}/api/logs?since=${since}`),
  tree: (kind = 'pptx') => jsonFetch(`${BASE}/api/tree?kind=${kind}`),

  run: (task, body = null) =>
    jsonFetch(`${BASE}/api/run/${task}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {})
    }),

  stop: () =>
    jsonFetch(`${BASE}/api/stop`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{}'
    }),

  sendReport: (label = 'Manual Report') =>
    jsonFetch(`${BASE}/api/report/email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ label })
    }),

  // ---- Auth ----
  me: () => jsonFetch(`${BASE}/api/me`),
  logout: () => jsonFetch(`${BASE}/api/logout`, { method: 'POST' }),
  login: (username, password) =>
    jsonFetch(`${BASE}/api/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    }),

  // ---- Admin ----
  dbStatus: () => jsonFetch(`${BASE}/api/db/status`),

  // ---- Downloads ----
  downloadUrl: (kind, path) =>
    `${BASE}/download/${kind}/${encodeURIComponent(path).replace(/%2F/g, '/')}`
}
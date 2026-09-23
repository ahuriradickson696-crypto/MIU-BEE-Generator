// api.js — thin wrapper around the Flask backend
const BASE = '' // Vite proxies /api/* to localhost:5000

async function jsonFetch(url, opts) {
  const r = await fetch(url, opts)
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${await r.text()}`)
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

  downloadUrl: (kind, path) =>
    `${BASE}/download/${kind}/${encodeURIComponent(path).replace(/%2F/g, '/')}`
}
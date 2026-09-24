// api.js — thin wrapper around the Flask backend
const BASE = import.meta.env.VITE_API_BASE_URL || 'https://miu-bee-api.onrender.com'

async function jsonFetch(url, opts = {}) {
  opts.credentials = 'include'

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 45000)
  opts.signal = controller.signal

  try {
    const r = await fetch(url, opts)
    if (!r.ok) {
      let msg = `HTTP ${r.status}`
      try {
        const data = await r.json()
        msg = data.error || data.message || msg
      } catch { /* not JSON */ }
      throw new Error(msg)
    }
    return await r.json()
  } finally {
    clearTimeout(timeoutId)
  }
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

  me: () => jsonFetch(`${BASE}/api/me`),
  logout: () => jsonFetch(`${BASE}/api/logout`, { method: 'POST' }),
  login: (username, password) =>
    jsonFetch(`${BASE}/api/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    }),

  changePassword: (oldPassword, newPassword) =>
    jsonFetch(`${BASE}/api/me/password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        old_password: oldPassword,
        new_password: newPassword
      })
    }),

  myLogins: () => jsonFetch(`${BASE}/api/me/logins`),
  dbStatus: () => jsonFetch(`${BASE}/api/db/status`),

  listUsers: () => jsonFetch(`${BASE}/api/users`),
  createUser: (payload) =>
    jsonFetch(`${BASE}/api/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }),
  updateUser: (username, payload) =>
    jsonFetch(`${BASE}/api/users/${encodeURIComponent(username)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }),
  deleteUser: (username) =>
    jsonFetch(`${BASE}/api/users/${encodeURIComponent(username)}`, {
      method: 'DELETE'
    }),
  resetPassword: (username, password) =>
    jsonFetch(`${BASE}/api/users/${encodeURIComponent(username)}/password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password })
    }),

  downloadUrl: (kind, path) =>
    `${BASE}/download/${kind}/${encodeURIComponent(path).replace(/%2F/g, '/')}`
}
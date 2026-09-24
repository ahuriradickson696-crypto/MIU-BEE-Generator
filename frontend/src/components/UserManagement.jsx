import React, { useEffect, useState } from 'react'
import {
  UserPlus, Trash2, KeyRound, X, Save, Shield, GraduationCap, Eye
} from 'lucide-react'
import { api } from '../api'
import { useAuth } from '../useAuth'

const ROLE_COLORS = {
  admin: '#00823C',
  lecturer: '#3B82F6',
  viewer: '#6B7280'
}

const ROLE_LABELS = {
  admin: '🛡️ admin',
  lecturer: '🎓 lecturer',
  viewer: '👁️ viewer'
}

export default function UserManagement({ onToast }) {
  const { user: me } = useAuth()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [resetFor, setResetFor] = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      const d = await api.listUsers()
      if (d.ok) setUsers(d.users || [])
      else onToast?.(d.error || 'Failed to load users', 'error')
    } catch (e) {
      onToast?.(`Error: ${e.message}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const changeRole = async (username, role) => {
    try {
      const d = await api.updateUser(username, { role })
      if (d.ok) {
        onToast?.(`${username} is now ${role}`, 'success')
        load()
      } else onToast?.(d.error || 'Failed', 'error')
    } catch (e) {
      onToast?.(`Error: ${e.message}`, 'error')
    }
  }

  const deleteUser = async (username) => {
    if (!confirm(`Delete user "${username}"? This cannot be undone.`)) return
    try {
      const d = await api.deleteUser(username)
      if (d.ok) {
        onToast?.(`Deleted ${username}`, 'success')
        load()
      } else onToast?.(d.error || 'Failed', 'error')
    } catch (e) {
      onToast?.(`Error: ${e.message}`, 'error')
    }
  }

  return (
    <div>
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        alignItems: 'center', marginBottom: 14
      }}>
        <div className="muted" style={{ fontSize: 12 }}>
          {users.length} user{users.length !== 1 ? 's' : ''} total
        </div>
        <button
          className="btn btn-green"
          style={{ width: 'auto', marginBottom: 0, padding: '8px 16px' }}
          onClick={() => setShowCreate(true)}
        >
          <UserPlus size={15} /> New User
        </button>
      </div>

      {loading ? (
        <div className="muted" style={{ padding: 12 }}>Loading users...</div>
      ) : (
        <div style={{
          border: '1px solid #E5E7EB', borderRadius: 8, overflow: 'hidden'
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: '#F9FAFB' }}>
                <th style={th}>Username</th>
                <th style={th}>Email</th>
                <th style={th}>Role</th>
                <th style={th}>Created</th>
                <th style={{ ...th, textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.username} style={{ borderTop: '1px solid #F3F4F6' }}>
                  <td style={td}>
                    <strong>{u.username}</strong>
                    {u.username === me?.username && (
                      <span style={{ color: '#9CA3AF', fontSize: 11, marginLeft: 6 }}>
                        (you)
                      </span>
                    )}
                  </td>
                  <td style={{ ...td, color: '#6B7280' }}>
                    {u.email || '—'}
                  </td>
                  <td style={td}>
                    <select
                      value={u.role}
                      onChange={(e) => changeRole(u.username, e.target.value)}
                      disabled={u.username === me?.username}
                      style={{
                        padding: '5px 10px', borderRadius: 6,
                        border: '1px solid #E5E7EB',
                        color: ROLE_COLORS[u.role] || '#374151',
                        fontWeight: 600, fontSize: 12.5,
                        fontFamily: 'inherit',
                        cursor: u.username === me?.username ? 'not-allowed' : 'pointer',
                        background: 'white',
                        opacity: u.username === me?.username ? .6 : 1
                      }}
                    >
                      <option value="admin">🛡️ admin</option>
                      <option value="lecturer">🎓 lecturer</option>
                      <option value="viewer">👁️ viewer</option>
                    </select>
                  </td>
                  <td style={{ ...td, color: '#9CA3AF', fontSize: 12 }}>
                    {u.created_at ? u.created_at.slice(0, 10) : '—'}
                  </td>
                  <td style={{ ...td, textAlign: 'right' }}>
                    <button
                      onClick={() => setResetFor(u.username)}
                      title="Reset password"
                      style={iconBtn('#3B82F6')}
                    >
                      <KeyRound size={13} />
                    </button>
                    <button
                      onClick={() => deleteUser(u.username)}
                      disabled={u.username === me?.username}
                      title={u.username === me?.username
                        ? 'Cannot delete yourself'
                        : 'Delete user'}
                      style={{
                        ...iconBtn('#C81E28'),
                        opacity: u.username === me?.username ? .4 : 1,
                        cursor: u.username === me?.username
                          ? 'not-allowed' : 'pointer'
                      }}
                    >
                      <Trash2 size={13} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showCreate && (
        <CreateUserModal
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false)
            load()
            onToast?.('User created', 'success')
          }}
          onToast={onToast}
        />
      )}

      {resetFor && (
        <ResetPasswordModal
          username={resetFor}
          onClose={() => setResetFor(null)}
          onDone={() => {
            setResetFor(null)
            onToast?.('Password reset', 'success')
          }}
          onToast={onToast}
        />
      )}
    </div>
  )
}


function CreateUserModal({ onClose, onCreated, onToast }) {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('viewer')
  const [saving, setSaving] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const d = await api.createUser({ username, email, password, role })
      if (d.ok) onCreated()
      else onToast?.(d.error || 'Failed', 'error')
    } catch (err) {
      onToast?.(`Error: ${err.message}`, 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal onClose={onClose} title="Create User">
      <form onSubmit={submit}>
        <Field label="Username">
          <input
            value={username}
            onChange={e => setUsername(e.target.value)}
            required
            autoFocus
            style={input}
          />
        </Field>
        <Field label="Email">
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            style={input}
            placeholder="optional"
          />
        </Field>
        <Field label="Password">
          <input
            type="text"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            minLength={6}
            style={input}
            placeholder="min 6 characters"
          />
        </Field>
        <Field label="Role">
          <select
            value={role}
            onChange={e => setRole(e.target.value)}
            style={input}
          >
            <option value="admin">🛡️ admin — full access</option>
            <option value="lecturer">🎓 lecturer — generate + download</option>
            <option value="viewer">👁️ viewer — view + download only</option>
          </select>
        </Field>
        <div style={{ display: 'flex', gap: 8, marginTop: 18 }}>
          <button
            type="button"
            className="btn btn-outline"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-green"
            disabled={saving}
          >
            <Save size={15} /> {saving ? 'Creating...' : 'Create User'}
          </button>
        </div>
      </form>
    </Modal>
  )
}


function ResetPasswordModal({ username, onClose, onDone, onToast }) {
  const [password, setPassword] = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const d = await api.resetPassword(username, password)
      if (d.ok) onDone()
      else onToast?.(d.error || 'Failed', 'error')
    } catch (err) {
      onToast?.(`Error: ${err.message}`, 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal onClose={onClose} title={`Reset password for ${username}`}>
      <form onSubmit={submit}>
        <Field label="New password">
          <input
            type="text"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            minLength={6}
            autoFocus
            style={input}
            placeholder="min 6 characters"
          />
        </Field>
        <div style={{ display: 'flex', gap: 8, marginTop: 18 }}>
          <button
            type="button"
            className="btn btn-outline"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-green"
            disabled={saving}
          >
            <KeyRound size={15} /> {saving ? 'Resetting...' : 'Reset'}
          </button>
        </div>
      </form>
    </Modal>
  )
}


function Modal({ children, title, onClose }) {
  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        background: 'rgba(0,0,0,.4)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 20
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'white', borderRadius: 12,
          padding: 24, width: '100%', maxWidth: 420,
          boxShadow: '0 20px 60px rgba(0,0,0,.25)'
        }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{
          display: 'flex', justifyContent: 'space-between',
          alignItems: 'center', marginBottom: 18
        }}>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#00823C' }}>
            {title}
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent', border: 'none',
              cursor: 'pointer', color: '#666'
            }}
          >
            <X size={18} />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}


function Field({ label, children }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{
        fontSize: 12, fontWeight: 600, color: '#374151', marginBottom: 5
      }}>
        {label}
      </div>
      {children}
    </div>
  )
}


// ---- styles ----
const th = {
  padding: '10px 12px',
  textAlign: 'left',
  fontWeight: 600,
  fontSize: 12.5,
  color: '#374151'
}

const td = {
  padding: '10px 12px',
  fontSize: 13
}

const input = {
  width: '100%', padding: '10px 12px',
  border: '1px solid #D5DBE0', borderRadius: 8,
  fontSize: 13.5, fontFamily: 'inherit', outline: 'none'
}

const iconBtn = (color) => ({
  background: 'transparent',
  border: '1px solid #E5E7EB',
  borderRadius: 6,
  padding: '5px 8px',
  marginRight: 6,
  cursor: 'pointer',
  color,
  display: 'inline-flex',
  alignItems: 'center'
})
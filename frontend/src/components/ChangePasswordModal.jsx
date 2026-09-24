import React, { useState } from 'react'
import { X, Save, KeyRound } from 'lucide-react'
import { api } from '../api'

export default function ChangePasswordModal({ onClose, onDone, onToast }) {
  const [oldPw, setOldPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')

    if (newPw !== confirmPw) {
      setError('New passwords do not match')
      return
    }
    if (newPw.length < 6) {
      setError('New password must be at least 6 characters')
      return
    }

    setSaving(true)
    try {
      const r = await api.changePassword(oldPw, newPw)
      if (r.ok) {
        onToast?.('Password changed successfully', 'success')
        onDone?.()
      } else {
        setError(r.message || 'Failed to change password')
      }
    } catch (err) {
      setError(err.message || 'Error')
    } finally {
      setSaving(false)
    }
  }

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
          <div style={{
            fontSize: 16, fontWeight: 700, color: '#00823C',
            display: 'flex', alignItems: 'center', gap: 8
          }}>
            <KeyRound size={18} /> Change Password
          </div>
          <button onClick={onClose} style={{
            background: 'transparent', border: 'none',
            cursor: 'pointer', color: '#666'
          }}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={submit}>
          <Field label="Current password">
            <input
              type="password" value={oldPw} required autoFocus
              onChange={e => setOldPw(e.target.value)}
              style={input}
            />
          </Field>

          <Field label="New password">
            <input
              type="password" value={newPw} required minLength={6}
              onChange={e => setNewPw(e.target.value)}
              style={input} placeholder="min 6 characters"
            />
          </Field>

          <Field label="Confirm new password">
            <input
              type="password" value={confirmPw} required minLength={6}
              onChange={e => setConfirmPw(e.target.value)}
              style={input}
            />
          </Field>

          {error && (
            <div style={{
              background: '#FEE2E2', color: '#991B1B',
              padding: '10px 12px', borderRadius: 8,
              fontSize: 13, marginBottom: 14
            }}>{error}</div>
          )}

          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            <button type="button" className="btn btn-outline" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-green" disabled={saving}>
              <Save size={15} /> {saving ? 'Saving...' : 'Change Password'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{
        fontSize: 12, fontWeight: 600, color: '#374151', marginBottom: 5
      }}>{label}</div>
      {children}
    </div>
  )
}

const input = {
  width: '100%', padding: '10px 12px',
  border: '1px solid #D5DBE0', borderRadius: 8,
  fontSize: 13.5, fontFamily: 'inherit', outline: 'none'
}
import React, { useEffect, useState } from 'react'
import { CheckCircle2, XCircle } from 'lucide-react'
import { api } from '../api'

export default function MyLogins() {
  const [logins, setLogins] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const d = await api.myLogins()
        if (d.ok) setLogins(d.logins || [])
      } catch { /* ignore */ }
      setLoading(false)
    }
    load()
  }, [])

  if (loading) {
    return <div className="muted" style={{ padding: 8 }}>Loading logins...</div>
  }

  if (logins.length === 0) {
    return <div className="muted" style={{ padding: 8 }}>No login history yet.</div>
  }

  return (
    <div style={{ fontSize: 12.5, maxHeight: 340, overflowY: 'auto' }}>
      {logins.map((l, i) => (
        <div key={i} style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '7px 10px',
          borderBottom: '1px solid #F3F4F6'
        }}>
          {l.success
            ? <CheckCircle2 size={14} color="#00823C" />
            : <XCircle size={14} color="#C81E28" />}
          <span style={{
            color: l.success ? '#00823C' : '#C81E28',
            fontWeight: 600, width: 60
          }}>
            {l.success ? 'Success' : 'Failed'}
          </span>
          <span style={{
            color: '#6B7280', flex: 1,
            fontFamily: 'monospace', fontSize: 11.5
          }}>
            {l.ip || '—'}
          </span>
          <span style={{ color: '#9CA3AF', fontSize: 11 }}>
            {l.ts ? l.ts.slice(0, 16).replace('T', ' ') : ''}
          </span>
        </div>
      ))}
    </div>
  )
}
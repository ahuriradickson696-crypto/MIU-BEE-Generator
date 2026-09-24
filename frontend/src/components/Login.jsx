import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { LogIn } from 'lucide-react'
import { useAuth } from '../useAuth.jsx'

export default function Login({ onSuccess }) {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const d = await login(username, password)
      if (d.ok) {
        onSuccess?.(d.user)
      } else {
        setError(d.error || 'Login failed')
      }
    } catch (err) {
      setError(err.message || 'Login error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'linear-gradient(135deg, #00823C 0%, #006B31 100%)',
      padding: 20
    }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        style={{
          width: '100%', maxWidth: 400,
          background: 'white', borderRadius: 14,
          padding: '36px 32px',
          boxShadow: '0 20px 60px rgba(0,0,0,.25)'
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{
            width: 64, height: 64, borderRadius: '50%',
            background: '#F0F8F3', margin: '0 auto 12px',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <LogIn size={28} color="#00823C" />
          </div>
          <div style={{ fontSize: 18, fontWeight: 700, color: '#1E1E1E' }}>
            MIU BEE Login
          </div>
          <div style={{ fontSize: 12, color: '#6B7280', marginTop: 4 }}>
            Sign in to continue
          </div>
        </div>

        <form onSubmit={submit}>
          <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>
            Username
          </label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoFocus
            required
            style={{
              width: '100%', padding: '11px 14px',
              border: '1px solid #D5DBE0', borderRadius: 8,
              fontSize: 14, fontFamily: 'inherit',
              marginTop: 6, marginBottom: 14, outline: 'none'
            }}
          />

          <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{
              width: '100%', padding: '11px 14px',
              border: '1px solid #D5DBE0', borderRadius: 8,
              fontSize: 14, fontFamily: 'inherit',
              marginTop: 6, marginBottom: 16, outline: 'none'
            }}
          />

          {error && (
            <div style={{
              background: '#FEE2E2', color: '#991B1B',
              padding: '10px 12px', borderRadius: 8,
              fontSize: 13, marginBottom: 14
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%', padding: '12px 16px',
              background: '#00823C', color: 'white',
              border: 'none', borderRadius: 8,
              fontSize: 14, fontWeight: 700,
              cursor: loading ? 'wait' : 'pointer',
              fontFamily: 'inherit',
              opacity: loading ? 0.7 : 1
            }}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div style={{
          marginTop: 18, textAlign: 'center',
          fontSize: 11, color: '#9CA3AF'
        }}>
          Metropolitan International University
        </div>
      </motion.div>
    </div>
  )
}
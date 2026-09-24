import { useEffect, useState, createContext, useContext } from 'react'
import { api } from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [authChecked, setAuthChecked] = useState(false)

  useEffect(() => {
    let mounted = true

    // Hard cap: force authChecked=true after 5 seconds no matter what
    const hardCap = setTimeout(() => {
      if (mounted) {
        console.log('[auth] 5s cap hit — showing login page')
        setAuthChecked(true)
      }
    }, 5000)

    const check = async () => {
      try {
        const d = await api.me()
        if (mounted && d && d.authenticated) setUser(d.user)
      } catch (e) {
        console.log('[auth] /api/me failed:', e.message)
      }
      if (mounted) {
        clearTimeout(hardCap)
        setAuthChecked(true)
      }
    }

    check()
    return () => { mounted = false; clearTimeout(hardCap) }
  }, [])

  const login = async (username, password) => {
    const d = await api.login(username, password)
    if (d.ok) setUser(d.user)
    return d
  }

  const logout = async () => {
    try { await api.logout() } catch {}
    setUser(null)
  }

  const can = (permission) => {
    if (!user) return false
    return (user.permissions || []).includes(permission)
  }

  const isAdmin = () => user?.role === 'admin'
  const isLecturer = () => user?.role === 'lecturer'
  const isViewer = () => user?.role === 'viewer'

  return (
    <AuthContext.Provider value={{
      user, authChecked, login, logout, can, isAdmin, isLecturer, isViewer
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}
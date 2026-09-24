import React, { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X } from 'lucide-react'
import { api } from './api'
import { useAuth } from './useAuth.jsx'
import { useTheme } from './useTheme'
import { useNotifications } from './useNotifications'

import StatCard from './components/StatCard'
import ProgressRing from './components/ProgressRing'
import LiveLog from './components/LiveLog'
import FileTree from './components/FileTree'
import Actions from './components/Actions'
import CourseTable from './components/CourseTable'
import Toasts from './components/Toasts'
import PrayerPage from './components/PrayerPage'
import SearchBar from './components/SearchBar'
import ZipButtons from './components/ZipButtons'
import Dashboard from './components/Dashboard'
import Login from './components/Login'
import UserManagement from './components/UserManagement'
import ChangePasswordModal from './components/ChangePasswordModal'
import MyLogins from './components/MyLogins'

const ROLE_LABELS = {
  admin: '🛡️ Admin',
  lecturer: '🎓 Lecturer',
  viewer: '👁️ Viewer'
}

export default function App() {
  const { user, authChecked, logout } = useAuth()
  const { theme, toggle } = useTheme()

  const [stats, setStats] = useState({
    total: 0, done: 0, remaining: 0, pptx: 0, pdf: 0,
    pct: 0, courses: [], running: false, task: null
  })
  const [logs, setLogs] = useState([])
  const [tree, setTree] = useState({ pptx: null, pdf: null, cache: null })
  const [treeTab, setTreeTab] = useState('pptx')
  const [toasts, setToasts] = useState([])
  const [showPrayer, setShowPrayer] = useState(
    () => localStorage.getItem('miu_bee_prayer_seen') !== 'yes'
  )
  const [view, setView] = useState('overview')
  const [adminTab, setAdminTab] = useState('main')
  const [showChangePw, setShowChangePw] = useState(false)
  const [showLogins, setShowLogins] = useState(false)

  const logIndexRef = useRef(0)

  const addToast = (msg, type = 'info') => {
    const id = Date.now() + Math.random()
    setToasts(t => [...t, { id, msg, type }])
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 4200)
  }

  const notif = useNotifications(stats, (result) => {
    if (result === 'granted') addToast('Notifications enabled 🔔', 'success')
    else addToast('Notifications blocked', 'error')
  })

  useEffect(() => {
    if (!user) return
    let mounted = true
    const tick = async () => {
      try {
        const s = await api.stats()
        if (mounted) setStats(s)
      } catch { /* ignore */ }
    }
    tick()
    const id = setInterval(tick, 2000)
    return () => { mounted = false; clearInterval(id) }
  }, [user])

  useEffect(() => {
    if (!user) return
    let mounted = true
    const tick = async () => {
      try {
        const { lines, next } = await api.logs(logIndexRef.current)
        if (mounted && lines.length) {
          logIndexRef.current = next
          setLogs(prev => [...prev, ...lines].slice(-2000))
        }
      } catch { /* ignore */ }
    }
    tick()
    const id = setInterval(tick, 1000)
    return () => { mounted = false; clearInterval(id) }
  }, [user])

  useEffect(() => {
    if (!user) return
    const fetchTrees = async () => {
      try {
        const [p, d, c] = await Promise.all([
          api.tree('pptx'), api.tree('pdf'), api.tree('cache')
        ])
        setTree({ pptx: p, pdf: d, cache: c })
      } catch { /* ignore */ }
    }
    fetchTrees()
    const id = setInterval(fetchTrees, 8000)
    return () => clearInterval(id)
  }, [user])

  const run = async (task, label) => {
    try {
      const res = await api.run(task)
      if (res.ok) addToast(`${label || task} started`, 'success')
      else addToast(res.message || res.error || 'Failed', 'error')
    } catch (e) {
      addToast(`${e.message}`, 'error')
    }
  }

  const stop = async () => {
    try { await api.stop(); addToast('Stopped', 'info') }
    catch { addToast('Stop failed', 'error') }
  }

  const sendReport = async () => {
    try {
      const r = await api.sendReport('Manual Report')
      addToast(r.message, r.ok ? 'success' : 'error')
    } catch (e) {
      addToast(`Email failed: ${e.message}`, 'error')
    }
  }

  const dismissPrayer = () => {
    localStorage.setItem('miu_bee_prayer_seen', 'yes')
    setShowPrayer(false)
  }

  if (!authChecked) {
    return (
      <div style={{
        minHeight: '100vh', display: 'flex',
        alignItems: 'center', justifyContent: 'center',
        background: '#F4F6F8', color: '#666', fontSize: 14
      }}>Loading...</div>
    )
  }

  if (!user) {
    return <Login onSuccess={() => { /* handled by AuthProvider */ }} />
  }

  if (showPrayer) {
    return <PrayerPage onEnter={dismissPrayer} />
  }

  const roleLabel = ROLE_LABELS[user.role] || user.role
  const pillBtn = {
    background: 'rgba(255,255,255,.18)',
    border: '1px solid rgba(255,255,255,.3)',
    color: 'white',
    padding: '8px 12px',
    borderRadius: 999,
    cursor: 'pointer',
    fontSize: 14,
    fontFamily: 'inherit',
    lineHeight: 1
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="header-brand">
            <div className="header-logo">
              <img src="/miu_logo.png" alt="MIU" />
            </div>
            <div>
              <h1>MIU BEE · Slide Generator</h1>
              <p>Metropolitan International University · Bachelor of Science in Electrical Engineering</p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <SearchBar onToast={addToast} />

            <button
              onClick={() => setView(v => v === 'overview' ? 'dashboard' : 'overview')}
              style={{
                background: 'rgba(255,255,255,.18)',
                border: '1px solid rgba(255,255,255,.3)',
                color: 'white',
                padding: '8px 16px',
                borderRadius: 999,
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: 600,
                fontFamily: 'inherit'
              }}
            >
              {view === 'overview' ? '📊 Dashboard' : '📋 Overview'}
            </button>

            {user.role === 'admin' && (
              <button
                onClick={() => setAdminTab(t => t === 'users' ? 'main' : 'users')}
                style={{
                  background: adminTab === 'users'
                    ? 'rgba(255,255,255,.35)'
                    : 'rgba(255,255,255,.18)',
                  border: '1px solid rgba(255,255,255,.3)',
                  color: 'white',
                  padding: '8px 16px',
                  borderRadius: 999,
                  cursor: 'pointer',
                  fontSize: 13,
                  fontWeight: 600,
                  fontFamily: 'inherit'
                }}
              >
                {adminTab === 'users' ? '📋 Back to App' : '👥 Manage Users'}
              </button>
            )}

            <AnimatePresence>
              {stats.running && stats.task && (
                <motion.div
                  className="task-badge"
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                >
                  <span className="dot" />
                  {stats.task}
                </motion.div>
              )}
            </AnimatePresence>

            {notif.supported && notif.permission !== 'granted' && (
              <button
                onClick={notif.requestPermission}
                title="Enable notifications"
                style={pillBtn}
              >
                🔔
              </button>
            )}

            <button
              onClick={toggle}
              title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
              style={pillBtn}
            >
              {theme === 'light' ? '🌙' : '☀️'}
            </button>

            <button
              onClick={() => setShowPrayer(true)}
              style={{
                background: 'rgba(255,255,255,.18)',
                border: '1px solid rgba(255,255,255,.3)',
                color: 'white',
                padding: '8px 16px',
                borderRadius: 999,
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: 600,
                fontFamily: 'inherit'
              }}
            >
              🙏 Prayer
            </button>

            <UserMenu
              user={user}
              roleLabel={roleLabel}
              onChangePassword={() => setShowChangePw(true)}
              onShowLogins={() => setShowLogins(true)}
              onLogout={logout}
            />
          </div>
        </div>
      </header>

      <main className="main">
        {user.role === 'admin' && adminTab === 'users' && (
          <div className="panel" style={{ marginBottom: 20 }}>
            <h2>User Management</h2>
            <UserManagement onToast={addToast} />
          </div>
        )}

        {adminTab === 'main' && (
        <>
        <motion.div
          className="stats-grid"
          initial="hidden"
          animate="visible"
          variants={{
            hidden: {},
            visible: { transition: { staggerChildren: 0.05 } }
          }}
        >
          <StatCard label="Topics" value={stats.total} sub="In curriculum" />
          <StatCard label="Completed" value={stats.done} sub="Cached & generated" />
          <StatCard label="Remaining" value={stats.remaining} sub="Still to do" color="danger" />
          <StatCard label="PPTX files" value={stats.pptx} sub="Slide decks" color="info" />
          <StatCard label="PDF files" value={stats.pdf} sub="Converted" color="amber" />
        </motion.div>

        <div className="columns">
          <div>
            <div className="panel" style={{ marginBottom: 20 }}>
              <h2>Overall Progress</h2>
              <ProgressRing percent={stats.pct} />
              <div className="progress-text" style={{ marginTop: 12 }}>
                <span>{stats.done} / {stats.total} topics</span>
                <span>{stats.pct}%</span>
              </div>
              <div className="progress-track">
                <div className="progress-fill" style={{ width: `${stats.pct}%` }} />
              </div>
            </div>

            <div className="panel">
              <h2>Actions</h2>
              <Actions
                running={stats.running}
                onGenerate={() => run('generate', 'Generate slides')}
                onProgress={() => run('progress', 'Check progress')}
                onPdf={() => run('pdf', 'Convert to PDF')}
                onRebuild={() => run('rebuild', 'Rebuild from cache')}
                onCleanup={() => run('cleanup', 'Cleanup (dry run)')}
                onCleanupApply={() => run('cleanup-apply', 'Cleanup (apply)')}
                onStop={stop}
                onReport={sendReport}
              />
            </div>
          </div>

          <div className="panel">
            <h2>Activity Log</h2>
            <LiveLog lines={logs} />
          </div>
        </div>

        <div className="panel" style={{ marginBottom: 20 }}>
          <h2>Downloads</h2>
          <ZipButtons pptxCount={stats.pptx} />
        </div>

        {view === 'dashboard' && (
          <div className="panel" style={{ marginBottom: 20 }}>
            <h2>Dashboard</h2>
            <Dashboard />
          </div>
        )}

        <div className="panel" style={{ marginBottom: 20 }}>
          <h2>Files</h2>
          <div className="tabs">
            <button className={`tab ${treeTab === 'pptx' ? 'active' : ''}`}
                    onClick={() => setTreeTab('pptx')}>Slides (.pptx)</button>
            <button className={`tab ${treeTab === 'pdf' ? 'active' : ''}`}
                    onClick={() => setTreeTab('pdf')}>PDFs (.pdf)</button>
            <button className={`tab ${treeTab === 'cache' ? 'active' : ''}`}
                    onClick={() => setTreeTab('cache')}>Cache (.json)</button>
          </div>
          <FileTree tree={tree[treeTab]} kind={treeTab} onToast={addToast} />
        </div>

        <div className="panel">
          <h2>Course Breakdown</h2>
          <CourseTable courses={stats.courses} />
        </div>
        </>
        )}
      </main>

      <Toasts items={toasts} />

      {showChangePw && (
        <ChangePasswordModal
          onClose={() => setShowChangePw(false)}
          onDone={() => setShowChangePw(false)}
          onToast={addToast}
        />
      )}

      {showLogins && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 1000,
          background: 'rgba(0,0,0,.4)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          padding: 20
        }} onClick={() => setShowLogins(false)}>
          <div style={{
            background: 'white', borderRadius: 12,
            padding: 24, width: '100%', maxWidth: 520
          }} onClick={e => e.stopPropagation()}>
            <div style={{
              display: 'flex', justifyContent: 'space-between',
              alignItems: 'center', marginBottom: 14
            }}>
              <div style={{ fontSize: 16, fontWeight: 700, color: '#00823C' }}>
                My Recent Logins
              </div>
              <button
                onClick={() => setShowLogins(false)}
                style={{
                  background: 'transparent', border: 'none',
                  cursor: 'pointer', color: '#666'
                }}
              >
                <X size={18} />
              </button>
            </div>
            <MyLogins />
          </div>
        </div>
      )}
    </div>
  )
}


function UserMenu({ user, roleLabel, onChangePassword, onShowLogins, onLogout }) {
  const [open, setOpen] = useState(false)

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen(o => !o)}
        title={`Signed in as ${user.username}`}
        style={{
          background: 'rgba(255,255,255,.18)',
          border: '1px solid rgba(255,255,255,.3)',
          color: 'white',
          padding: '8px 16px',
          borderRadius: 999,
          cursor: 'pointer',
          fontSize: 13,
          fontWeight: 600,
          fontFamily: 'inherit',
          display: 'flex',
          alignItems: 'center',
          gap: 6
        }}
      >
        <span>{roleLabel}</span>
        <span style={{ opacity: .75 }}>·</span>
        <span>{user.username}</span>
        <span style={{ opacity: .75, fontSize: 10 }}>{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <>
          <div
            onClick={() => setOpen(false)}
            style={{ position: 'fixed', inset: 0, zIndex: 200 }}
          />
          <div style={{
            position: 'absolute', top: 'calc(100% + 6px)', right: 0,
            background: 'white', borderRadius: 10,
            boxShadow: '0 12px 32px rgba(0,0,0,.18)',
            minWidth: 220, padding: 6, zIndex: 201
          }}>
            <MenuItem onClick={() => { setOpen(false); onChangePassword() }}>
              🔐 Change Password
            </MenuItem>
            <MenuItem onClick={() => { setOpen(false); onShowLogins() }}>
              📜 My Recent Logins
            </MenuItem>
            <div style={{ height: 1, background: '#F3F4F6', margin: '4px 0' }} />
            <MenuItem onClick={onLogout} danger>⎋ Logout</MenuItem>
          </div>
        </>
      )}
    </div>
  )
}

function MenuItem({ children, onClick, danger }) {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'block', width: '100%', textAlign: 'left',
        background: 'transparent', border: 'none',
        padding: '9px 12px', borderRadius: 6,
        cursor: 'pointer', fontSize: 13.5,
        fontFamily: 'inherit',
        color: danger ? '#C81E28' : '#374151'
      }}
      onMouseOver={(e) => { e.currentTarget.style.background = '#F9FAFB' }}
      onMouseOut={(e) => { e.currentTarget.style.background = 'transparent' }}
    >
      {children}
    </button>
  )
}
import React, { useEffect, useState } from 'react'
import { History as HistoryIcon, ChevronRight, ChevronDown, Clock, FileText, Eye, Download } from 'lucide-react'
import { api } from '../api'

export default function History({ onToast }) {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [openCourse, setOpenCourse] = useState(null)
  const [courseHistory, setCourseHistory] = useState({})
  const [openTopic, setOpenTopic] = useState(null)
  const [previewContent, setPreviewContent] = useState(null)

  useEffect(() => { load() }, [])

  const load = async () => {
    setLoading(true)
    try {
      const r = await fetch('/api/history/stats', { credentials: 'include' })
      const d = await r.json()
      if (d.ok) setStats(d)
      else onToast?.(d.error || 'Failed to load history', 'error')
    } catch (e) {
      onToast?.(`Error: ${e.message}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  const toggleCourse = async (course_code) => {
    if (openCourse === course_code) {
      setOpenCourse(null)
      return
    }
    setOpenCourse(course_code)
    if (!courseHistory[course_code]) {
      // Load history for each topic under this course — we'll fetch per-topic on demand
      setCourseHistory(h => ({ ...h, [course_code]: [] }))
    }
  }

  const loadTopic = async (course_code, topic_number) => {
    const key = `${course_code}__${topic_number}`
    if (openTopic === key) {
      setOpenTopic(null)
      return
    }
    setOpenTopic(key)
    try {
      const r = await fetch(
        `/api/history/${encodeURIComponent(course_code)}/${topic_number}`,
        { credentials: 'include' }
      )
      const d = await r.json()
      if (d.ok) setCourseHistory(h => ({ ...h, [key]: d.history }))
      else onToast?.(d.error || 'Failed', 'error')
    } catch (e) {
      onToast?.(`Error: ${e.message}`, 'error')
    }
  }

  if (loading) {
    return <div className="muted" style={{ padding: 12 }}>Loading history...</div>
  }

  if (!stats || stats.total_archived === 0) {
    return (
      <div style={{
        padding: 24, textAlign: 'center',
        background: '#F9FAFB', borderRadius: 10,
        border: '1px dashed #D5DBE0'
      }}>
        <HistoryIcon size={36} color="#9CA3AF" style={{ margin: '0 auto 12px', display: 'block' }} />
        <div style={{ fontSize: 14, fontWeight: 600, color: '#374151' }}>
          No history yet
        </div>
        <div style={{ fontSize: 12.5, color: '#6B7280', marginTop: 6, maxWidth: 420, margin: '6px auto 0' }}>
          When you regenerate a topic that already exists, the previous version is
          automatically archived here. Nothing is ever lost.
        </div>
      </div>
    )
  }

  return (
    <div>
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        alignItems: 'center', marginBottom: 14
      }}>
        <div className="muted" style={{ fontSize: 12 }}>
          {stats.total_archived} archived version{stats.total_archived !== 1 ? 's' : ''}
        </div>
        <button
          className="btn btn-outline"
          style={{ width: 'auto', marginBottom: 0, padding: '6px 12px', fontSize: 12.5 }}
          onClick={load}
        >
          Refresh
        </button>
      </div>

      <div style={{ border: '1px solid #E5E7EB', borderRadius: 8, overflow: 'hidden' }}>
        {stats.by_course.map((c) => (
          <div key={c.course_code} style={{ borderTop: '1px solid #F3F4F6' }}>
            <button
              onClick={() => toggleCourse(c.course_code)}
              style={{
                width: '100%', textAlign: 'left',
                background: openCourse === c.course_code ? '#F0F8F3' : 'white',
                border: 'none', padding: '12px 14px',
                cursor: 'pointer', fontFamily: 'inherit',
                display: 'flex', alignItems: 'center', gap: 10,
                fontSize: 13.5
              }}
            >
              {openCourse === c.course_code ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              <strong style={{ color: '#00823C', flex: 1 }}>{c.course_code}</strong>
              <span style={{
                background: '#E8F5EE', color: '#00823C',
                padding: '2px 10px', borderRadius: 999,
                fontSize: 11.5, fontWeight: 600
              }}>
                {c.count} version{c.count !== 1 ? 's' : ''}
              </span>
            </button>

            {openCourse === c.course_code && (
              <div style={{ padding: '8px 14px 14px', background: '#FAFBFC' }}>
                <div className="muted" style={{ fontSize: 12, marginBottom: 8 }}>
                  Enter a topic number to see its archived versions.
                  (Topic numbers correspond to the order in the curriculum, starting at 1.)
                </div>
                <TopicLookup
                  course_code={c.course_code}
                  onLookup={(n) => loadTopic(c.course_code, n)}
                  onToast={onToast}
                />

                {Object.entries(courseHistory)
                  .filter(([k]) => k.startsWith(c.course_code + '__'))
                  .map(([k, versions]) => {
                    const [_, tn] = k.split('__')
                    const isOpen = openTopic === k
                    return (
                      <div key={k} style={{ marginTop: 12 }}>
                        <button
                          onClick={() => setOpenTopic(isOpen ? null : k)}
                          style={{
                            background: 'white', border: '1px solid #E5E7EB',
                            borderRadius: 6, padding: '8px 12px',
                            cursor: 'pointer', fontFamily: 'inherit',
                            fontSize: 12.5, width: '100%', textAlign: 'left',
                            display: 'flex', alignItems: 'center', gap: 8
                          }}
                        >
                          <FileText size={14} color="#00823C" />
                          <span style={{ fontWeight: 600 }}>Topic #{tn}</span>
                          <span style={{ color: '#6B7280' }}>
                            ({versions.length} archived)
                          </span>
                        </button>

                        {isOpen && versions.length > 0 && (
                          <div style={{ marginTop: 8 }}>
                            {versions.map((v, i) => (
                              <div
                                key={i}
                                style={{
                                  background: 'white',
                                  border: '1px solid #E5E7EB',
                                  borderRadius: 6,
                                  padding: '10px 12px',
                                  marginBottom: 6,
                                  fontSize: 12.5
                                }}
                              >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                    <Clock size={12} color="#6B7280" />
                                    <span style={{ color: '#374151' }}>
                                      {v.archived_at ? v.archived_at.slice(0, 16).replace('T', ' ') : '—'}
                                    </span>
                                  </div>
                                  <button
                                    onClick={() => setPreviewContent(v)}
                                    style={{
                                      background: 'transparent', border: '1px solid #E5E7EB',
                                      borderRadius: 6, padding: '3px 8px',
                                      cursor: 'pointer', fontSize: 11.5,
                                      display: 'flex', alignItems: 'center', gap: 4,
                                      color: '#00823C', fontFamily: 'inherit'
                                    }}
                                  >
                                    <Eye size={11} /> Preview
                                  </button>
                                </div>
                                <div style={{ color: '#6B7280', marginTop: 4 }}>
                                  {v.topic} · {v.course_name}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )
                  })}
              </div>
            )}
          </div>
        ))}
      </div>

      {previewContent && (
        <PreviewModal data={previewContent} onClose={() => setPreviewContent(null)} />
      )}
    </div>
  )
}


function TopicLookup({ course_code, onLookup, onToast }) {
  const [val, setVal] = useState('')
  return (
    <div style={{ display: 'flex', gap: 6 }}>
      <input
        type="number"
        min="1"
        value={val}
        onChange={(e) => setVal(e.target.value)}
        placeholder="Topic number (e.g. 1)"
        style={{
          flex: 1, padding: '7px 10px',
          border: '1px solid #D5DBE0', borderRadius: 6,
          fontSize: 12.5, fontFamily: 'inherit', outline: 'none'
        }}
      />
      <button
        onClick={() => {
          const n = parseInt(val, 10)
          if (!n || n < 1) { onToast?.('Enter a valid topic number', 'error'); return }
          onLookup(n)
        }}
        style={{
          background: '#00823C', color: 'white', border: 'none',
          borderRadius: 6, padding: '7px 14px',
          cursor: 'pointer', fontSize: 12.5, fontWeight: 600,
          fontFamily: 'inherit'
        }}
      >
        View
      </button>
    </div>
  )
}


function PreviewModal({ data, onClose }) {
  const slides = (data.content && data.content.slides) || []
  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: 'rgba(0,0,0,.5)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 20
    }} onClick={onClose}>
      <div style={{
        background: 'white', borderRadius: 12,
        padding: 20, width: '100%', maxWidth: 720,
        maxHeight: '85vh', display: 'flex', flexDirection: 'column'
      }} onClick={e => e.stopPropagation()}>
        <div style={{
          display: 'flex', justifyContent: 'space-between',
          alignItems: 'flex-start', marginBottom: 14
        }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#00823C' }}>
              {data.topic}
            </div>
            <div style={{ fontSize: 12, color: '#6B7280', marginTop: 2 }}>
              {data.course_name} · archived {data.archived_at ? data.archived_at.slice(0, 16).replace('T', ' ') : ''}
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', cursor: 'pointer', fontSize: 18, color: '#666' }}
          >
            ×
          </button>
        </div>

        <div style={{ overflowY: 'auto', flex: 1 }}>
          {slides.length === 0 ? (
            <div className="muted">No slide content in this archive.</div>
          ) : (
            slides.map((s, i) => (
              <div key={i} style={{
                border: '1px solid #E5E7EB', borderRadius: 8,
                padding: '12px 14px', marginBottom: 10
              }}>
                <div style={{ fontWeight: 600, color: '#00823C', marginBottom: 6, fontSize: 13 }}>
                  {i + 1}. {s.title}
                </div>
                <ul style={{ margin: 0, paddingLeft: 20, fontSize: 12.5, color: '#374151', lineHeight: 1.6 }}>
                  {(s.bullets || []).map((b, j) => <li key={j}>{b}</li>)}
                </ul>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
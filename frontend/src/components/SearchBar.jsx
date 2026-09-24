import React, { useState, useEffect, useRef } from 'react'
import { Search, X } from 'lucide-react'
import { api } from '../api'

export default function SearchBar({ onToast }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const wrapRef = useRef(null)
  const debounceRef = useRef(null)

  // Close when clicking outside
  useEffect(() => {
    const handler = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)

    const q = query.trim()
    if (!q) {
      setResults(null)
      return
    }

    debounceRef.current = setTimeout(async () => {
      setLoading(true)
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`)
        const data = await res.json()
        if (data.ok) {
          setResults(data)
          setOpen(true)
        } else {
          onToast?.(data.error || 'Search failed', 'error')
        }
      } catch (e) {
        onToast?.(`Search error: ${e.message}`, 'error')
      } finally {
        setLoading(false)
      }
    }, 300)

    return () => clearTimeout(debounceRef.current)
  }, [query, onToast])

  const clear = () => {
    setQuery('')
    setResults(null)
    setOpen(false)
  }

  return (
    <div ref={wrapRef} style={{ position: 'relative', width: 320 }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        background: 'rgba(255,255,255,.18)',
        border: '1px solid rgba(255,255,255,.3)',
        padding: '7px 12px', borderRadius: 999
      }}>
        <Search size={15} color="white" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results && setOpen(true)}
          placeholder="Search courses, topics..."
          style={{
            flex: 1, background: 'transparent', border: 'none',
            color: 'white', outline: 'none',
            fontSize: 13, fontFamily: 'inherit'
          }}
        />
        {query && (
          <button onClick={clear} style={{
            background: 'transparent', border: 'none',
            color: 'white', cursor: 'pointer', padding: 0, display: 'flex'
          }}>
            <X size={14} />
          </button>
        )}
      </div>

      {open && results && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 8px)', right: 0,
          width: 480, maxHeight: 420, overflowY: 'auto',
          background: 'white', borderRadius: 10,
          boxShadow: '0 12px 32px rgba(0,0,0,.18)',
          zIndex: 100, padding: 8
        }}>
          {results.count === 0 ? (
            <div style={{ padding: 16, color: '#6B7280', fontSize: 13, textAlign: 'center' }}>
              No results for "{query}"
            </div>
          ) : (
            <>
              {results.courses?.length > 0 && (
                <div>
                  <div style={{
                    fontSize: 11, fontWeight: 700, color: '#00823C',
                    textTransform: 'uppercase', letterSpacing: .6,
                    padding: '8px 10px 4px'
                  }}>Courses ({results.courses.length})</div>
                  {results.courses.map((c, i) => (
                    <div key={i} style={{
                      padding: '8px 10px', borderRadius: 6,
                      fontSize: 13, borderBottom: '1px solid #F3F4F6'
                    }}>
                      <div style={{ fontWeight: 600, color: '#00823C' }}>{c.code}</div>
                      <div style={{ color: '#374151' }}>{c.name}</div>
                      <div style={{ fontSize: 11, color: '#6B7280', marginTop: 2 }}>
                        Year {c.year} · Sem {c.semester} · {c.topics?.length || 0} topics
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {results.topics?.length > 0 && (
                <div>
                  <div style={{
                    fontSize: 11, fontWeight: 700, color: '#00823C',
                    textTransform: 'uppercase', letterSpacing: .6,
                    padding: '10px 10px 4px'
                  }}>Generated Topics ({results.topics.length})</div>
                  {results.topics.map((t, i) => (
                    <div key={i} style={{
                      padding: '8px 10px', borderRadius: 6,
                      fontSize: 13, borderBottom: '1px solid #F3F4F6'
                    }}>
                      <div style={{ fontWeight: 600 }}>{t.topic}</div>
                      <div style={{ fontSize: 11, color: '#6B7280', marginTop: 2 }}>
                        {t.course_code} · {t.course_name} · Y{t.year}S{t.semester}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
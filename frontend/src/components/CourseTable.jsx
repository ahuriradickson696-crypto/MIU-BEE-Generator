import React, { useState, useMemo } from 'react'

export default function CourseTable({ courses }) {
  const [filter, setFilter] = useState('all')

  const filtered = useMemo(() => {
    if (!courses) return []
    if (filter === 'done') return courses.filter(c => c.done === c.total && c.total > 0)
    if (filter === 'partial') return courses.filter(c => c.done > 0 && c.done < c.total)
    if (filter === 'todo') return courses.filter(c => c.done === 0)
    return courses
  }, [courses, filter])

  const grouped = useMemo(() => {
    const map = new Map()
    filtered.forEach(c => {
      const key = `Year ${c.year} · Semester ${c.semester}`
      if (!map.has(key)) map.set(key, [])
      map.get(key).push(c)
    })
    return Array.from(map.entries())
  }, [filtered])

  if (!courses || courses.length === 0) {
    return <div className="muted" style={{ padding: 8 }}>No courses loaded.</div>
  }

  return (
    <div>
      <div className="row" style={{ marginBottom: 12 }}>
        <button className={`btn ${filter === 'all' ? 'btn-green' : 'btn-outline'}`}
                onClick={() => setFilter('all')}>
          All ({courses.length})
        </button>
        <button className={`btn ${filter === 'done' ? 'btn-green' : 'btn-outline'}`}
                onClick={() => setFilter('done')}>
          Done ({courses.filter(c => c.done === c.total && c.total > 0).length})
        </button>
        <button className={`btn ${filter === 'partial' ? 'btn-green' : 'btn-outline'}`}
                onClick={() => setFilter('partial')}>
          In Progress ({courses.filter(c => c.done > 0 && c.done < c.total).length})
        </button>
        <button className={`btn ${filter === 'todo' ? 'btn-green' : 'btn-outline'}`}
                onClick={() => setFilter('todo')}>
          To Do ({courses.filter(c => c.done === 0).length})
        </button>
      </div>

      <div style={{ maxHeight: 460, overflowY: 'auto' }}>
        {grouped.map(([header, rows]) => (
          <div key={header} style={{ marginBottom: 18 }}>
            <div
              style={{
                background: '#E8F5EE',
                color: '#00823C',
                fontWeight: 700,
                padding: '8px 12px',
                borderRadius: 6,
                fontSize: 12.5,
                letterSpacing: 0.3
              }}
            >
              {header}
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <tbody>
                {rows.map(c => {
                  const pct = c.total ? Math.round(c.done / c.total * 100) : 0
                  const color = pct === 100 ? '#00823C' : pct > 0 ? '#E8A93C' : '#C81E28'
                  return (
                    <tr key={c.code}>
                      <td style={{ padding: '6px 8px', borderBottom: '1px solid #F3F4F6', width: 90, fontWeight: 600 }}>
                        {c.code}
                      </td>
                      <td style={{ padding: '6px 8px', borderBottom: '1px solid #F3F4F6' }}>
                        {c.name}
                      </td>
                      <td style={{ padding: '6px 8px', borderBottom: '1px solid #F3F4F6', textAlign: 'center', width: 90 }}>
                        <span style={{ color, fontWeight: 600 }}>
                          {c.done}/{c.total}
                        </span>
                      </td>
                      <td style={{ padding: '6px 8px', borderBottom: '1px solid #F3F4F6', width: 160 }}>
                        <div style={{ height: 6, background: '#E9ECEF', borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{ width: `${pct}%`, height: '100%', background: color, transition: 'width .5s' }} />
                        </div>
                      </td>
                      <td style={{ padding: '6px 8px', borderBottom: '1px solid #F3F4F6', textAlign: 'right', width: 60, color: '#6B7280' }}>
                        {pct}%
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        ))}
      </div>
    </div>
  )
}
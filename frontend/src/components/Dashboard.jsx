import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell, Legend
} from 'recharts'
import { api } from '../api'

const GREEN = '#00823C'
const RED = '#C81E28'
const AMBER = '#E8A93C'
const COLORS = ['#00823C', '#00A64E', '#3B82F6', '#E8A93C', '#C81E28', '#8B5CF6', '#EC4899', '#14B8A6']

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch('/api/dashboard')
        const json = await res.json()
        if (json.ok) setData(json)
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
    const id = setInterval(fetchData, 15000)
    return () => clearInterval(id)
  }, [])

  if (loading) {
    return <div className="muted" style={{ padding: 12 }}>Loading dashboard...</div>
  }
  if (!data || !data.charts) {
    return <div className="muted" style={{ padding: 12 }}>Dashboard unavailable.</div>
  }

  const { stats, charts } = data
  const daily = charts.daily || []
  const byYear = charts.by_year || []

  const completionData = [
    { name: 'Completed', value: stats.done, color: GREEN },
    { name: 'Remaining', value: stats.remaining, color: AMBER }
  ]

  return (
    <div>
      {/* Stat summary row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
        gap: 12, marginBottom: 20
      }}>
        <MiniStat label="Total Topics" value={stats.total} color={GREEN} />
        <MiniStat label="Completed" value={stats.done} color={GREEN} />
        <MiniStat label="Remaining" value={stats.remaining} color={RED} />
        <MiniStat label="PPTX Files" value={stats.pptx} color="#3B82F6" />
        <MiniStat label="PDF Files" value={stats.pdf} color={AMBER} />
      </div>

      {/* Charts row */}
      <div className="charts-row">
        {/* Daily generation */}
        <div style={{ background: 'white', borderRadius: 10, padding: 16 }}>
          <div style={{
            fontSize: 12, fontWeight: 700, color: GREEN,
            textTransform: 'uppercase', letterSpacing: .6, marginBottom: 12
          }}>
            Topics Generated (last 14 days)
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={daily}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F0" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }}
                     tickFormatter={(d) => d.slice(5)} />
              <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 6 }} />
              <Line type="monotone" dataKey="count" stroke={GREEN}
                    strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Completion pie */}
        <div style={{ background: 'white', borderRadius: 10, padding: 16 }}>
          <div style={{
            fontSize: 12, fontWeight: 700, color: GREEN,
            textTransform: 'uppercase', letterSpacing: .6, marginBottom: 12
          }}>
            Overall Completion
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={completionData} dataKey="value"
                   nameKey="name" cx="50%" cy="50%"
                   innerRadius={55} outerRadius={85}
                   paddingAngle={2}>
                {completionData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 6 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* By year bar + recent activity */}
      <div className="charts-row" style={{ marginTop: 20 }}>
        <div style={{ background: 'white', borderRadius: 10, padding: 16 }}>
          <div style={{
            fontSize: 12, fontWeight: 700, color: GREEN,
            textTransform: 'uppercase', letterSpacing: .6, marginBottom: 12
          }}>
            Topics by Year
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={byYear}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F0" />
              <XAxis dataKey="year" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 6 }} />
              <Bar dataKey="count" fill={GREEN} radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div style={{ background: 'white', borderRadius: 10, padding: 16 }}>
          <div style={{
            fontSize: 12, fontWeight: 700, color: GREEN,
            textTransform: 'uppercase', letterSpacing: .6, marginBottom: 12
          }}>
            Recent Activity
          </div>
          <div style={{ maxHeight: 220, overflowY: 'auto', fontSize: 12 }}>
            {(charts.recent || []).length === 0 ? (
              <div className="muted" style={{ padding: 8 }}>No activity yet.</div>
            ) : (
              charts.recent.map((a, i) => (
                <div key={i} style={{
                  padding: '6px 8px', borderBottom: '1px solid #F3F4F6',
                  display: 'flex', justifyContent: 'space-between', gap: 8
                }}>
                  <span style={{ color: '#374151', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    <strong style={{ color: GREEN }}>{a.action}</strong> · {a.detail}
                  </span>
                  <span style={{ color: '#9CA3AF', fontSize: 11, flexShrink: 0 }}>
                    {a.ts ? a.ts.slice(0, 16).replace('T', ' ') : ''}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function MiniStat({ label, value, color }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        background: 'white', borderRadius: 10, padding: '12px 16px',
        borderLeft: `4px solid ${color}`
      }}
    >
      <div style={{ fontSize: 10, color: '#6B7280', textTransform: 'uppercase', letterSpacing: .5 }}>
        {label}
      </div>
      <div style={{ fontSize: 22, fontWeight: 700, color, marginTop: 4 }}>
        {value}
      </div>
    </motion.div>
  )
}
import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

export default function StatCard({ label, value, sub, color = 'default' }) {
  const [display, setDisplay] = useState(0)

  // Animate number counting up
  useEffect(() => {
    const target = typeof value === 'number' ? value : 0
    if (target === display) return
    const diff = target - display
    const step = Math.max(1, Math.ceil(Math.abs(diff) / 25))
    let current = display
    const id = setInterval(() => {
      current += diff > 0 ? step : -step
      if ((diff > 0 && current >= target) || (diff < 0 && current <= target)) {
        current = target
        clearInterval(id)
      }
      setDisplay(current)
    }, 20)
    return () => clearInterval(id)
    // eslint-disable-next-line
  }, [value])

  return (
    <motion.div
      className={`stat-card ${color === 'danger' ? 'danger' : color === 'info' ? 'info' : color === 'amber' ? 'amber' : ''}`}
      variants={{
        hidden: { opacity: 0, y: 10 },
        visible: { opacity: 1, y: 0 }
      }}
    >
      <div className="stat-label">{label}</div>
      <div className="stat-value">{display}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </motion.div>
  )
}
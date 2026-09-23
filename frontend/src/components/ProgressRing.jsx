import React, { useEffect, useState } from 'react'

export default function ProgressRing({ percent = 0, size = 140, stroke = 12 }) {
  const [animated, setAnimated] = useState(0)

  useEffect(() => {
    let raf
    const start = performance.now()
    const from = animated
    const to = percent
    const dur = 700
    const tick = (now) => {
      const t = Math.min(1, (now - start) / dur)
      const eased = 1 - Math.pow(1 - t, 3)
      setAnimated(from + (to - from) * eased)
      if (t < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
    // eslint-disable-next-line
  }, [percent])

  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const dash = (animated / 100) * circumference

  return (
    <div style={{ display: 'flex', justifyContent: 'center', position: 'relative' }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#E9ECEF"
          strokeWidth={stroke}
          fill="none"
        />
        <defs>
          <linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#00823C" />
            <stop offset="100%" stopColor="#00A64E" />
          </linearGradient>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="url(#ringGrad)"
          strokeWidth={stroke}
          strokeLinecap="round"
          fill="none"
          strokeDasharray={`${dash} ${circumference}`}
        />
      </svg>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          pointerEvents: 'none'
        }}
      >
        <div style={{ fontSize: 26, fontWeight: 700, color: '#00823C' }}>
          {Math.round(animated)}%
        </div>
        <div style={{ fontSize: 11, color: '#6B7280', marginTop: 2 }}>Complete</div>
      </div>
    </div>
  )
}
import React, { useEffect, useRef } from 'react'

export default function LiveLog({ lines }) {
  const ref = useRef(null)
  const autoscroll = useRef(true)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    if (autoscroll.current) {
      el.scrollTop = el.scrollHeight
    }
  }, [lines])

  const onScroll = () => {
    const el = ref.current
    if (!el) return
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40
    autoscroll.current = nearBottom
  }

  return (
    <div className="log" ref={ref} onScroll={onScroll}>
      {lines.length === 0
        ? <span className="log-empty">Welcome. Click any action to start.</span>
        : lines.join('')}
    </div>
  )
}
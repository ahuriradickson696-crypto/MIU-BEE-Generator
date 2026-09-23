import React from 'react'
import { AnimatePresence, motion } from 'framer-motion'

export default function Toasts({ items }) {
  return (
    <div className="toast-stack">
      <AnimatePresence>
        {items.map(t => (
          <motion.div
            key={t.id}
            className={`toast ${t.type === 'error' ? 'error' : t.type === 'info' ? 'info' : ''}`}
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 30 }}
            transition={{ duration: 0.22 }}
          >
            {t.msg}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
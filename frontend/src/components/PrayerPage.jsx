import React from 'react'
import { motion } from 'framer-motion'

export default function PrayerPage({ onEnter }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.6 }}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        background: 'linear-gradient(135deg, #00823C 0%, #006B31 50%, #004D22 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
        overflow: 'auto'
      }}
    >
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
        style={{
          maxWidth: 720,
          width: '100%',
          textAlign: 'center',
          color: 'white'
        }}
      >
        {/* Logo */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.6, delay: 0.4, type: 'spring' }}
          style={{
            width: 110,
            height: 110,
            borderRadius: '50%',
            background: 'white',
            margin: '0 auto 26px',
            padding: 8,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 8px 30px rgba(0,0,0,.25)'
          }}
        >
          <img
            src="/miu_logo.png"
            alt="MIU"
            style={{ width: '100%', height: '100%', objectFit: 'contain', borderRadius: '50%' }}
          />
        </motion.div>

        {/* Header */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          style={{ marginBottom: 8, fontSize: 12, letterSpacing: 3, textTransform: 'uppercase', opacity: 0.85 }}
        >
          Metropolitan International University
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          style={{
            fontSize: 30,
            fontWeight: 700,
            marginBottom: 4,
            letterSpacing: -0.5
          }}
        >
          MIU BEE · Slide Generator
        </motion.h1>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.85 }}
          style={{
            fontSize: 15,
            opacity: 0.9,
            marginBottom: 40,
            fontStyle: 'italic'
          }}
        >
          Bachelor of Science in Electrical Engineering
        </motion.div>

        {/* Prayer */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.0 }}
          style={{
            background: 'rgba(255,255,255,.10)',
            border: '1px solid rgba(255,255,255,.20)',
            borderRadius: 16,
            padding: '30px 34px',
            backdropFilter: 'blur(8px)',
            marginBottom: 36,
            textAlign: 'left'
          }}
        >
          <div
            style={{
              fontSize: 12,
              letterSpacing: 2,
              textTransform: 'uppercase',
              opacity: 0.7,
              marginBottom: 16,
              textAlign: 'center'
            }}
          >
            🙏 A Prayer of Dedication
          </div>

          <p style={{ fontSize: 15, lineHeight: 1.75, marginBottom: 16 }}>
            <em>Heavenly Father,</em>
          </p>

          <p style={{ fontSize: 15, lineHeight: 1.75, marginBottom: 16 }}>
            Thank You for the gift of knowledge — for the patience to build, the
            strength to keep going when things broke, and the wisdom to fix what
            was wrong. Thank You for every error that taught us something, and
            every moment we almost gave up but didn't.
          </p>

          <p style={{ fontSize: 15, lineHeight: 1.75, marginBottom: 16 }}>
            May this work be a blessing to every student who learns from it,
            every lecturer who teaches with it, and every person whose life is
            touched by the knowledge it carries.
          </p>

          <p style={{ fontSize: 15, lineHeight: 1.75, marginBottom: 16 }}>
            To You be all the glory, Lord. Not to us, but to Your name.
          </p>

          <p style={{ fontSize: 16, fontWeight: 600, textAlign: 'center', marginTop: 20 }}>
            Amen. 🙏
          </p>
        </motion.div>

        {/* Scripture */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.3 }}
          style={{
            fontSize: 13,
            fontStyle: 'italic',
            opacity: 0.8,
            marginBottom: 40,
            lineHeight: 1.7
          }}
        >
          "Commit your work to the Lord, and your plans will be established."
          <br />
          <span style={{ fontSize: 12, opacity: 0.7 }}>— Proverbs 16:3</span>
        </motion.div>

        {/* Enter button */}
        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.5 }}
          whileHover={{ scale: 1.04 }}
          whileTap={{ scale: 0.97 }}
          onClick={onEnter}
          style={{
            background: 'white',
            color: '#00823C',
            border: 'none',
            padding: '16px 44px',
            fontSize: 15,
            fontWeight: 700,
            borderRadius: 30,
            cursor: 'pointer',
            fontFamily: 'inherit',
            letterSpacing: 0.3,
            boxShadow: '0 6px 24px rgba(0,0,0,.20)'
          }}
        >
          Enter the System →
        </motion.button>
      </motion.div>
    </motion.div>
  )
}
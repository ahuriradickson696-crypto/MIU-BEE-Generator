import React from 'react'
import { Package, PackageOpen } from 'lucide-react'

export default function ZipButtons({ pptxCount }) {
  const hasSlides = pptxCount > 0

  const downloadAll = () => {
    window.open('/api/zip/all', '_blank')
  }

  return (
    <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
      <button
        className="btn btn-outline"
        onClick={downloadAll}
        disabled={!hasSlides}
        style={{ marginBottom: 0 }}
        title={hasSlides ? 'Download all slide decks as ZIP' : 'No slides yet'}
      >
        <Package size={16} /> Download All as ZIP
      </button>
    </div>
  )
}
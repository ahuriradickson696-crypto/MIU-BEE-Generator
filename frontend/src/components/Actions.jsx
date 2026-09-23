import React from 'react'
import {
  Play, BarChart3, FileDown, RotateCcw, Trash2, StopCircle, Mail
} from 'lucide-react'

export default function Actions({
  running,
  onGenerate, onProgress, onPdf, onRebuild,
  onCleanup, onCleanupApply, onStop, onReport
}) {
  const d = running

  return (
    <div>
      <button className="btn btn-green" onClick={onGenerate} disabled={d}>
        <Play size={16} /> Generate All Slides
      </button>

      <button className="btn btn-gray" onClick={onProgress} disabled={d}>
        <BarChart3 size={16} /> Check Progress
      </button>

      <button className="btn btn-gray" onClick={onPdf} disabled={d}>
        <FileDown size={16} /> Convert to PDF
      </button>

      <button className="btn btn-gray" onClick={onRebuild} disabled={d}>
        <RotateCcw size={16} /> Rebuild from Cache
      </button>

      <button className="btn btn-gray" onClick={onCleanup} disabled={d}>
        <Trash2 size={16} /> Cleanup (dry run)
      </button>

      <button className="btn btn-red" onClick={onCleanupApply} disabled={d}>
        <Trash2 size={16} /> Cleanup (DELETE)
      </button>

      <button className="btn btn-outline" onClick={onReport} disabled={d}>
        <Mail size={16} /> Email Report Now
      </button>

      <button className="btn btn-red" onClick={onStop} disabled={!running}>
        <StopCircle size={16} /> STOP Current Run
      </button>
    </div>
  )
}
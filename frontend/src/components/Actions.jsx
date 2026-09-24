import React from 'react'
import {
  Play, BarChart3, FileDown, RotateCcw, Trash2, StopCircle, Mail
} from 'lucide-react'
import { useAuth } from '../useAuth'

export default function Actions({
  running,
  onGenerate, onProgress, onPdf, onRebuild,
  onCleanup, onCleanupApply, onStop, onReport
}) {
  const { can, user } = useAuth()
  const d = running

  return (
    <div>
      {can('generate') && (
        <button className="btn btn-green" onClick={onGenerate} disabled={d}>
          <Play size={16} /> Generate All Slides
        </button>
      )}

      {can('progress') && (
        <button className="btn btn-gray" onClick={onProgress} disabled={d}>
          <BarChart3 size={16} /> Check Progress
        </button>
      )}

      {can('pdf') && (
        <button className="btn btn-gray" onClick={onPdf} disabled={d}>
          <FileDown size={16} /> Convert to PDF
        </button>
      )}

      {can('rebuild') && (
        <button className="btn btn-gray" onClick={onRebuild} disabled={d}>
          <RotateCcw size={16} /> Rebuild from Cache
        </button>
      )}

      {can('cleanup') && (
        <button className="btn btn-gray" onClick={onCleanup} disabled={d}>
          <Trash2 size={16} /> Cleanup (dry run)
        </button>
      )}

      {can('cleanup_apply') && (
        <button className="btn btn-red" onClick={onCleanupApply} disabled={d}>
          <Trash2 size={16} /> Cleanup (DELETE)
        </button>
      )}

      {can('report') && (
        <button className="btn btn-outline" onClick={onReport} disabled={d}>
          <Mail size={16} /> Email Report Now
        </button>
      )}

      {can('stop') && (
        <button className="btn btn-red" onClick={onStop} disabled={!running}>
          <StopCircle size={16} /> STOP Current Run
        </button>
      )}

      {/* Friendly message for view-only users */}
      {!can('generate') && !can('stop') && !can('cleanup') && (
        <div
          className="muted"
          style={{
            padding: 14,
            background: '#F0F8F3',
            border: '1px solid #C7E6D2',
            borderRadius: 8,
            fontSize: 12.5,
            lineHeight: 1.6,
            color: '#006B31'
          }}
        >
          👁️ <strong>View-only access</strong>
          {user?.role && <span> ({user.role})</span>}
          <br />
          You can browse, search, and download slides.
          Contact an administrator if you need generation rights.
        </div>
      )}
    </div>
  )
}
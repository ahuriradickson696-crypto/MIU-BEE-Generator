import React, { useState } from 'react'
import { ChevronRight, ChevronDown, Folder, FileText, Download } from 'lucide-react'
import { api } from '../api'

function Node({ node, kind, path = '', depth = 0, onToast }) {
  const [open, setOpen] = useState(depth < 4)

  if (!node || !node.children) return null

  if (node.type === 'file') {
    const fullPath = path ? `${path}/${node.name}` : node.name
    return (
      <a
        className="tree-file"
        href={api.downloadUrl(kind === 'pptx' ? 'pptx' : 'pdf', fullPath)}
        target="_blank"
        rel="noreferrer"
      >
        <FileText size={13} />
        <span>{node.name}</span>
      </a>
    )
  }

  const isFolder = node.type === 'folder'
  const isEmpty = isFolder && node.children.length === 0
  const nextPath = path ? `${path}/${node.name}` : node.name

  return (
    <div className="tree-node">
      <div
        className="tree-folder"
        onClick={() => setOpen(o => !o)}
        style={{ cursor: isFolder ? 'pointer' : 'default' }}
      >
        {isFolder ? (
          open ? <ChevronDown size={14} /> : <ChevronRight size={14} />
        ) : null}
        <Folder size={14} color={isFolder ? '#00823C' : '#9CA3AF'} />
        <span>{node.name}</span>
        {isEmpty && <span className="muted" style={{ marginLeft: 6 }}>(empty)</span>}
      </div>

      {open && !isEmpty && (
        <div className="tree-children">
          {node.children.map((child, i) => (
            <Node
              key={child.name + i}
              node={child}
              kind={kind}
              path={nextPath}
              depth={depth + 1}
              onToast={onToast}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function FileTree({ tree, kind, onToast }) {
  if (!tree || !tree.children || tree.children.length === 0) {
    const msg = kind === 'pptx'
      ? 'No PPTX files yet.'
      : kind === 'pdf'
        ? 'No PDF files yet.'
        : 'No cache files yet.'
    return <div className="muted" style={{ padding: 8 }}>{msg}</div>
  }

  return (
    <div className="tree">
      <Node node={tree} kind={kind} onToast={onToast} />
    </div>
  )
}
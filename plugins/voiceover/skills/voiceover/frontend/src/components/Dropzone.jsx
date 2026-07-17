import { useState } from 'react'
import { UploadCloud, FileText } from 'lucide-react'

// Drag-and-drop + click-to-browse file picker.
// The clickable surface is a <label> that *contains* the file input, so a click
// opens the OS picker natively — no programmatic input.click(), which avoids the
// bubble loop that otherwise reopened the picker after a file was chosen.
export default function Dropzone({ accept, file, onFile }) {
  const [over, setOver] = useState(false)

  const accepted = accept.split(',').map((s) => s.trim().toLowerCase())
  const matches = (f) => accepted.some((ext) => f.name.toLowerCase().endsWith(ext))

  const handleFiles = (files) => {
    const f = files?.[0]
    if (f && matches(f)) onFile(f)
  }

  return (
    <label
      className={`relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-8 text-center transition-colors ${
        over
          ? 'border-brand-blue bg-brand-tint'
          : 'border-line bg-slate-50 hover:border-brand-blue/60'
      }`}
      onDragOver={(e) => {
        e.preventDefault()
        setOver(true)
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setOver(false)
        handleFiles(e.dataTransfer.files)
      }}
    >
      <input
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      {file ? (
        <div className="flex items-center gap-3">
          <FileText className="h-7 w-7 flex-shrink-0 text-brand-600" />
          <div className="text-left">
            <p className="text-sm font-semibold text-navy">{file.name}</p>
            <p className="text-xs text-muted">
              {(file.size / 1024 / 1024).toFixed(1)} MB · click to replace
            </p>
          </div>
        </div>
      ) : (
        <>
          <UploadCloud className="mb-2 h-8 w-8 text-muted" />
          <p className="text-sm font-medium text-slate">
            Drag a deck here, or <span className="text-brand-700">browse</span>
          </p>
        </>
      )}
    </label>
  )
}

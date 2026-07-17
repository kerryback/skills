import { useRef, useState } from 'react'
import { X } from 'lucide-react'
import { api } from '../api'
import { Button, Field, inputClass } from './ui'
import { useToast } from './Toast'
import Dropzone from './Dropzone'

const ACCEPT = '.pdf'

export default function NewProjectDialog({
  onClose,
  onCreated,
  onSessionExpired,
}) {
  const [name, setName] = useState('')
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const nameEdited = useRef(false)
  const toast = useToast()

  const pick = (f) => {
    setFile(f)
    if (!nameEdited.current && f) {
      setName(f.name.replace(/\.[^.]+$/, ''))
    }
  }

  const submit = async (e) => {
    e.preventDefault()
    if (!file || !name.trim()) return
    setError('')
    setBusy(true)
    try {
      const proj = await api.createProject(name.trim(), file)
      toast.success(`Created "${proj.name}". Converting…`)
      onCreated(proj)
    } catch (err) {
      if (err.status === 401) return onSessionExpired()
      setError(err.message || 'Upload failed.')
      setBusy(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-navy/40 px-4 py-8 backdrop-blur-sm"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-lg animate-fadein rounded-2xl bg-white p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-extrabold tracking-tight text-navy">
            New deck
          </h2>
          <button
            onClick={onClose}
            className="text-muted hover:text-slate"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={submit} className="space-y-4">
          <Field label="Name" hint="Shown to you only">
            <input
              className={inputClass}
              value={name}
              onChange={(e) => {
                nameEdited.current = true
                setName(e.target.value)
              }}
              placeholder="e.g. Intro to Options — Session 3"
              required
            />
          </Field>

          <Field
            label="Slide deck"
            hint="PDF only — export PowerPoint/Keynote decks to PDF first"
          >
            <Dropzone accept={ACCEPT} file={file} onFile={pick} />
          </Field>

          {error && (
            <p className="text-sm text-red-600" role="alert">
              {error}
            </p>
          )}

          <div className="flex justify-end gap-2 pt-1">
            <Button variant="subtle" type="button" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              loading={busy}
              disabled={!file || !name.trim()}
            >
              Upload &amp; convert
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

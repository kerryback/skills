import { useCallback, useEffect, useState } from 'react'
import { Plus } from 'lucide-react'
import { api } from '../api'
import { Button, Card, Spinner, StatePill, ErrorBanner } from './ui'
import NewProjectDialog from './NewProjectDialog'

export default function ProjectsView({ onOpen, onSessionExpired }) {
  const [projects, setProjects] = useState(null)
  const [error, setError] = useState('')
  const [creating, setCreating] = useState(false)
  const [selected, setSelected] = useState('')

  const load = useCallback(async () => {
    setError('')
    try {
      const list = await api.listProjects()
      setProjects(list)
    } catch (err) {
      if (err.status === 401) return onSessionExpired()
      setError(err.message)
      setProjects([])
    }
  }, [onSessionExpired])

  useEffect(() => {
    load()
  }, [load])

  const selectedProject = (projects || []).find((p) => p.id === selected)

  return (
    <div className="mx-auto max-w-3xl px-5 py-10">
      <div className="mb-6">
        <h1 className="text-2xl font-extrabold tracking-tight text-navy">
          Make a narrated video
        </h1>
        <p className="mt-2 text-sm text-muted">
          Turn a PDF slide deck into a narrated MP4 plus a transcript. Claude Code
          writes the narration; you pick a voice and generate. Each deck is saved
          by name, so you can reopen it later to edit and regenerate.
        </p>
        <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm text-muted">
          <li>Add a PDF slide deck (in PowerPoint, use Export to PDF).</li>
          <li>Claude Code drafts the narration; you review and revise it.</li>
          <li>Pick an ElevenLabs voice (including your own cloned voices) and generate.</li>
          <li>Preview the video; the MP4 and transcript are saved to your working folder.</li>
        </ol>
      </div>

      <ErrorBanner message={error} onRetry={load} />

      <Card className="p-6">
        <Button size="lg" onClick={() => setCreating(true)}>
          <Plus className="h-4 w-4" /> New deck
        </Button>

        {projects == null ? (
          <div className="mt-6 flex items-center gap-2 text-muted">
            <Spinner className="h-5 w-5 text-brand-blue" /> Loading decks…
          </div>
        ) : projects.length === 0 ? (
          <p className="mt-6 text-sm text-muted">
            No decks yet. Add one above, or launch the skill on a PDF.
          </p>
        ) : (
          <div className="mt-6">
            <label
              htmlFor="deck-select"
              className="mb-1.5 block text-sm font-semibold text-navy"
            >
              Open an existing deck
            </label>
            <div className="flex items-center gap-2">
              <select
                id="deck-select"
                value={selected}
                onChange={(e) => setSelected(e.target.value)}
                className="min-w-0 flex-1 rounded-xl border border-line bg-white px-3 py-2.5 text-sm text-slate focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
              >
                <option value="">Select a deck…</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                    {p.stale ? ' — needs regenerating' : ''}
                  </option>
                ))}
              </select>
              <Button
                variant="primary"
                onClick={() => selected && onOpen(selected)}
                disabled={!selected}
              >
                Open
              </Button>
            </div>
            {selectedProject && (
              <div className="mt-2">
                <StatePill state={selectedProject.state} stale={selectedProject.stale} />
              </div>
            )}
            <p className="mt-3 text-xs text-muted">
              To delete a deck, remove its folder from{' '}
              <code>.voiceover/decks</code> in your project folder.
            </p>
          </div>
        )}
      </Card>

      {creating && (
        <NewProjectDialog
          onClose={() => setCreating(false)}
          onCreated={(proj) => {
            setCreating(false)
            onOpen(proj.id)
          }}
          onSessionExpired={onSessionExpired}
        />
      )}
    </div>
  )
}

import { useCallback, useEffect, useState } from 'react'
import { AlertTriangle, FileText, Headphones, RotateCw } from 'lucide-react'
import { api } from './api'
import { JOB_TERMINALS } from './constants'
import { useJobEvents } from './hooks/useJobEvents'
import { ToastProvider, useToast } from './components/Toast'
import { Button, Card, ErrorBanner, ProgressBar, Spinner, StatePill } from './components/ui'
import ApiKeyBanner from './components/ApiKeyBanner'
import DeckView from './components/DeckView'

// The launcher opens the app at /?project=<id>. There is no home screen and no
// in-app upload: a deck is two files in the instructor's own folder, so it is
// opened by launching the skill on it, not by picking it here.
const initialProject = () =>
  new URLSearchParams(window.location.search).get('project') || null

// How often to re-read the deck's state. This is how notes drafted by Claude,
// and edits made in Quarto or PowerPoint, announce themselves.
const POLL_MS = 4000

function Shell() {
  const [projectId, setProjectId] = useState(initialProject)
  const [project, setProject] = useState(null)
  const [error, setError] = useState('')
  const { progress, running, start } = useJobEvents()
  const toast = useToast()

  const refresh = useCallback(async () => {
    if (!projectId) return null
    try {
      const p = await api.getProject(projectId)
      setProject(p)
      setError('')
      return p
    } catch (err) {
      setError(err.message)
      return null
    }
  }, [projectId])

  useEffect(() => {
    refresh()
    const iv = setInterval(refresh, POLL_MS)
    return () => clearInterval(iv)
  }, [refresh])

  const reload = useCallback(async () => {
    if (!projectId) return
    try {
      await api.reload(projectId)
      start(projectId, {
        terminals: JOB_TERMINALS.load,
        onDone: async () => {
          const p = await refresh()
          const n = p?.slides?.length || 0
          const narrated = (p?.slides || []).filter((s) => s.notes?.trim()).length
          toast.success(`Reloaded — ${n} slides, ${narrated} with notes.`)
        },
        onError: async () => {
          await refresh()
          toast.error("Couldn't read the deck.")
        },
      })
    } catch (err) {
      toast.error(err.message)
    }
  }, [projectId, refresh, start, toast])

  if (!projectId) return <NoDeck onOpen={setProjectId} />

  return (
    <div className="min-h-full flex flex-col">
      <TopBar project={project} onReload={reload} reloading={running} />
      <ApiKeyBanner />
      <main className="mx-auto w-full max-w-[1600px] flex-1 px-5 py-5">
        <ErrorBanner message={error} onRetry={refresh} />

        {!project ? (
          <div className="flex items-center justify-center py-24 text-muted">
            <Spinner className="h-6 w-6 text-brand-blue" />
          </div>
        ) : (
          <div className="space-y-3">
            <FileNotices project={project} onReload={reload} />

            {running && (
              <Card className="p-4">
                <ProgressBar progress={progress} />
              </Card>
            )}

            {project.state === 'load_failed' ? (
              <LoadFailed project={project} onReload={reload} />
            ) : project.state === 'loading' && !project.slides?.length ? (
              <div className="flex items-center justify-center gap-2 py-24 text-muted">
                <Spinner className="h-5 w-5 text-brand-blue" /> Reading the deck…
              </div>
            ) : (
              <DeckView project={project} refresh={refresh} />
            )}
          </div>
        )}
      </main>
    </div>
  )
}

function TopBar({ project, onReload, reloading }) {
  const files = project?.files
  return (
    <header className="sticky top-0 z-30 border-b border-navy/40 bg-navy text-white">
      <div className="mx-auto flex max-w-[1600px] flex-wrap items-center justify-between gap-3 px-5 py-2.5">
        <div className="flex min-w-0 items-center gap-2.5">
          <span className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-white/10">
            <Headphones className="h-4 w-4" />
          </span>
          <div className="min-w-0">
            <span className="block truncate text-sm font-extrabold leading-tight tracking-tight">
              {project?.name || 'Voiceover'}
            </span>
            {files?.source && (
              <span
                className="block truncate text-[0.7rem] text-white/60"
                title={files.source_dir}
              >
                {files.source} + {files.pdf}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {project && <StatePill state={project.state} stale={project.stale} />}
          <Button
            variant="ghost"
            size="sm"
            className="border-white/30 text-white hover:bg-white/10"
            onClick={onReload}
            loading={reloading}
            title="Re-read the deck and its PDF from disk"
          >
            <RotateCw className="h-4 w-4" /> Reload
          </Button>
        </div>
      </div>
    </header>
  )
}

// The two ways the pair of files goes quietly wrong: one of them changed since
// the app read it, or the PDF is older than the deck it supposedly came from —
// which is how new notes end up narrating old slides.
function FileNotices({ project, onReload }) {
  const f = project.files || {}
  const changed = f.source_changed || f.pdf_changed
  if (!changed && !f.pdf_older_than_source && !f.source_missing && !f.pdf_missing)
    return null

  if (f.source_missing || f.pdf_missing) {
    return (
      <Notice tone="red">
        {f.source_missing ? f.source : f.pdf} is no longer where the app found it.
        Put it back, or relaunch the skill on the deck's new location.
      </Notice>
    )
  }

  return (
    <Notice
      tone={changed ? 'brand' : 'amber'}
      action={
        <Button variant="subtle" size="sm" onClick={onReload}>
          <RotateCw className="h-4 w-4" /> Reload
        </Button>
      }
    >
      {changed ? (
        <>
          {[f.source_changed && f.source, f.pdf_changed && f.pdf]
            .filter(Boolean)
            .join(' and ')}{' '}
          changed on disk since this was read.
        </>
      ) : (
        <>
          {f.pdf} is older than {f.source}. If you edited the slides, re-export
          the PDF — otherwise the video will show the old slides.
        </>
      )}
    </Notice>
  )
}

function Notice({ tone, children, action }) {
  const tones = {
    brand: 'border-brand-200 bg-brand-50/70 text-slate',
    amber: 'border-amber-200 bg-amber-50 text-amber-800',
    red: 'border-red-200 bg-red-50 text-red-700',
  }
  return (
    <div
      className={`flex flex-wrap items-center justify-between gap-3 rounded-xl border px-4 py-2.5 text-sm ${tones[tone]}`}
    >
      <span className="flex items-center gap-2">
        <AlertTriangle className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
        {children}
      </span>
      {action}
    </div>
  )
}

// A load failure is nearly always the slide-count check, and its message says
// what to go fix — so show it plainly rather than as a stack trace.
function LoadFailed({ project, onReload }) {
  const message = (project.log || '').split('\n')[0]
  return (
    <Card className="p-6">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-600" />
        <div className="min-w-0 flex-1">
          <h2 className="text-base font-extrabold tracking-tight text-navy">
            Couldn&apos;t read this deck
          </h2>
          <p className="mt-1.5 whitespace-pre-wrap text-sm text-slate">
            {message || 'The deck could not be read.'}
          </p>
          <div className="mt-4">
            <Button onClick={onReload}>
              <RotateCw className="h-4 w-4" /> Try again
            </Button>
          </div>
        </div>
      </div>
    </Card>
  )
}

// Opening the app bare (no ?project=) isn't the normal path, but it shouldn't be
// a dead end: list the decks this folder already knows about.
function NoDeck({ onOpen }) {
  const [decks, setDecks] = useState(null)
  useEffect(() => {
    api
      .listProjects()
      .then(setDecks)
      .catch(() => setDecks([]))
  }, [])

  return (
    <div className="mx-auto max-w-2xl px-5 py-16">
      <h1 className="text-2xl font-extrabold tracking-tight text-navy">
        Voiceover
      </h1>
      <p className="mt-2 text-sm text-muted">
        A deck is two files you keep yourself: the one you wrote — a Quarto
        <code className="mx-1">.qmd</code> or a
        <code className="mx-1">.pptx</code>, where the speaker notes live — and
        the PDF you exported from it, which supplies the slide images. Open one
        by launching the skill on it; ask Claude, or run{' '}
        <code>skill_launch.py lecture.qmd</code>.
      </p>

      {decks === null ? (
        <div className="mt-6 flex items-center gap-2 text-muted">
          <Spinner className="h-5 w-5 text-brand-blue" /> Loading…
        </div>
      ) : decks.length === 0 ? (
        <p className="mt-6 text-sm text-muted">No decks opened yet.</p>
      ) : (
        <Card className="mt-6 divide-y divide-line">
          {decks.map((d) => (
            <button
              key={d.id}
              onClick={() => onOpen(d.id)}
              className="flex w-full items-center gap-3 px-4 py-3 text-left transition hover:bg-slate-50"
            >
              <FileText className="h-4 w-4 flex-shrink-0 text-muted" />
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-semibold text-navy">
                  {d.name}
                </span>
                <span className="block truncate text-xs text-muted">
                  {d.files?.source}
                </span>
              </span>
              <StatePill state={d.state} stale={d.stale} />
            </button>
          ))}
        </Card>
      )}
    </div>
  )
}

export default function App() {
  return (
    <ToastProvider>
      <Shell />
    </ToastProvider>
  )
}

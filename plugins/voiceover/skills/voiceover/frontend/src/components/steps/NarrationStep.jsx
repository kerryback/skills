import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ArrowLeft, ArrowRight, Check } from 'lucide-react'
import { api, toRel } from '../../api'
import { estimateSeconds } from '../../constants'
import { useToast } from '../Toast'
import { Button, ErrorBanner, Spinner, StepHeader } from '../ui'

const AUTOSAVE_MS = 900
// Narration the Claude Code agent writes lands via the API, so re-poll to show
// it live. Small payload; a few-second cadence is plenty.
const POLL_MS = 3000

export default function NarrationStep({ project, goTo }) {
  const toast = useToast()

  const [slides, setSlides] = useState(null)
  const [current, setCurrent] = useState(0)
  const [error, setError] = useState('')
  const [saveState, setSaveState] = useState('idle')

  const timers = useRef({})
  const pending = useRef({})

  const imageByIndex = useMemo(() => {
    const m = {}
    ;(project.slides || []).forEach((s) => {
      m[s.index] = toRel(s.image_url)
    })
    return m
  }, [project.slides])

  const loadNarration = useCallback(async () => {
    const data = await api.getNarration(project.id)
    setSlides((prev) => {
      const fresh = data.slides || []
      if (!prev) return fresh
      // Preserve any locally-unsaved edits (index present in pending), so a poll
      // that arrives mid-typing never clobbers the instructor's own edit.
      return fresh.map((s) =>
        pending.current[s.index] !== undefined
          ? { ...s, narration: pending.current[s.index] }
          : s
      )
    })
  }, [project.id])

  // Initial load, then poll so narration written by the agent appears without a
  // manual refresh.
  useEffect(() => {
    let cancelled = false
    loadNarration().catch((err) => !cancelled && setError(err.message))
    const iv = setInterval(() => {
      loadNarration().catch(() => {})
    }, POLL_MS)
    return () => {
      cancelled = true
      clearInterval(iv)
    }
  }, [loadNarration])

  useEffect(() => {
    return () => Object.values(timers.current).forEach(clearTimeout)
  }, [])

  // ---- autosave (manual edits) ----
  const flush = useCallback(
    async (index) => {
      const text = pending.current[index]
      if (text === undefined) return
      delete pending.current[index]
      setSaveState('saving')
      try {
        await api.saveNarration(project.id, index, text)
        setSaveState((s) => (s === 'saving' ? 'saved' : s))
      } catch (err) {
        setSaveState('error')
        toast.error(`Autosave failed: ${err.message}`)
      }
    },
    [project.id, toast]
  )

  const flushNow = useCallback(
    (index) => {
      clearTimeout(timers.current[index])
      return flush(index)
    },
    [flush]
  )

  const onEdit = (index, text) => {
    setSlides((prev) =>
      prev.map((s) => (s.index === index ? { ...s, narration: text } : s))
    )
    pending.current[index] = text
    setSaveState('dirty')
    clearTimeout(timers.current[index])
    timers.current[index] = setTimeout(() => flush(index), AUTOSAVE_MS)
  }

  const goToIndex = async (i) => {
    const s = slides?.[current]
    if (s) await flushNow(s.index)
    setCurrent(i)
  }

  if (error && !slides) {
    return (
      <div className="animate-fadein">
        <StepHeader step="2 · Narration" title="Narration" />
        <ErrorBanner message={error} />
      </div>
    )
  }

  if (!slides) {
    return (
      <div className="flex items-center justify-center py-24 text-muted">
        <Spinner className="h-6 w-6 text-brand-blue" />
      </div>
    )
  }

  const slide = slides[current]
  const { words, seconds } = estimateSeconds(slide?.narration)

  return (
    <div className="animate-fadein">
      <StepHeader
        step="2 · Narration"
        title="Narration"
        subtitle="Claude Code writes and revises this narration — just ask it in chat (“draft narration for the deck,” “tighten slide 3,” “warmer tone”). Edits appear here live, and you can also tweak any slide directly. Changes autosave."
        right={
          <div className="flex items-center gap-2">
            <SaveIndicator state={saveState} />
            <Button
              onClick={async () => {
                if (slide) await flushNow(slide.index)
                goTo('generate')
              }}
            >
              Continue to Generate <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        }
      />

      {/* Editor cluster: rail · preview · editor */}
      <div className="grid gap-3 lg:grid-cols-[150px_minmax(0,1fr)_minmax(0,1fr)]">
        {/* Slide rail */}
        <div className="scroll-thin h-[64vh] space-y-1.5 overflow-y-auto rounded-xl border border-slate-200/60 bg-white p-2 shadow-sm">
          {slides.map((s, i) => {
            const est = estimateSeconds(s.narration)
            const empty = !s.narration?.trim()
            return (
              <button
                key={s.index}
                onClick={() => goToIndex(i)}
                className={`flex w-full items-start gap-2 rounded-lg border-l-2 p-1.5 text-left transition-colors ${
                  i === current
                    ? 'border-brand-600 bg-brand-50'
                    : 'border-transparent hover:bg-slate-50'
                }`}
              >
                {imageByIndex[s.index] ? (
                  <img
                    src={imageByIndex[s.index]}
                    alt=""
                    loading="lazy"
                    className="h-9 w-14 flex-shrink-0 rounded border border-line object-cover"
                  />
                ) : (
                  <span className="flex h-9 w-14 flex-shrink-0 items-center justify-center rounded border border-line bg-slate-50 text-xs text-muted">
                    {i + 1}
                  </span>
                )}
                <span className="min-w-0 pt-0.5">
                  <span
                    className={`block truncate text-xs font-semibold ${
                      i === current ? 'text-navy' : 'text-slate'
                    }`}
                  >
                    {s.title || `Slide ${i + 1}`}
                  </span>
                  <span
                    className={`text-[0.7rem] ${empty ? 'text-amber-600' : 'text-muted'}`}
                  >
                    {empty ? 'No narration' : `~${est.seconds}s`}
                  </span>
                </span>
              </button>
            )
          })}
        </div>

        {/* Slide preview */}
        <div className="flex h-[64vh] flex-col rounded-xl border border-slate-200/60 bg-white p-3 shadow-sm">
          <div className="flex flex-1 items-center justify-center overflow-hidden rounded-lg bg-slate-50">
            {imageByIndex[slide.index] ? (
              <img
                src={imageByIndex[slide.index]}
                alt={`Slide ${current + 1}`}
                className="max-h-full max-w-full object-contain"
              />
            ) : (
              <div className="flex items-center justify-center text-muted">
                Slide {current + 1}
              </div>
            )}
          </div>
          <div className="mt-2 flex items-center justify-between px-1 text-xs text-muted">
            <span>
              Slide {current + 1} of {slides.length}
            </span>
            <span className="truncate pl-2 font-medium text-slate">
              {slide.title}
            </span>
          </div>
        </div>

        {/* Editor */}
        <div className="flex h-[64vh] flex-col">
          <div className="mb-1.5 flex items-baseline justify-between">
            <span className="text-sm font-semibold text-navy">Narration</span>
            <span className="text-xs text-muted tabular-nums">
              {words} words · ~{seconds} sec
            </span>
          </div>
          <textarea
            value={slide.narration || ''}
            onChange={(e) => onEdit(slide.index, e.target.value)}
            onBlur={() => flushNow(slide.index)}
            placeholder="Empty — ask Claude Code to draft the narration, or write it here yourself."
            className="scroll-thin w-full flex-1 resize-none rounded-xl border border-line bg-white p-4 text-sm leading-relaxed text-slate focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
          />
          <div className="mt-3 flex justify-between">
            <Button
              variant="subtle"
              size="sm"
              disabled={current === 0}
              onClick={() => goToIndex(current - 1)}
            >
              <ArrowLeft className="h-4 w-4" /> Previous
            </Button>
            <Button
              variant="subtle"
              size="sm"
              disabled={current === slides.length - 1}
              onClick={() => goToIndex(current + 1)}
            >
              Next <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

function SaveIndicator({ state }) {
  const map = {
    idle: ['text-muted', ''],
    dirty: ['text-muted', 'Unsaved changes…'],
    saving: ['text-brand-dark', 'Saving…'],
    saved: ['text-green-600', 'All changes saved'],
    error: ['text-red-600', 'Save failed'],
  }
  const [cls, label] = map[state] || map.idle
  if (!label) return null
  return (
    <span className={`flex items-center gap-1.5 text-xs font-medium ${cls}`}>
      {state === 'saving' && <Spinner className="h-3 w-3" />}
      {state === 'saved' && <Check className="h-3.5 w-3.5" strokeWidth={3} />}
      {label}
    </span>
  )
}

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ArrowLeft, ArrowRight, Check } from 'lucide-react'
import { api, toRel } from '../../api'
import { CHANGE_LABELS, estimateSeconds } from '../../constants'
import { useToast } from '../Toast'
import { Button, ErrorBanner, ReviewSummary, Spinner, StepHeader } from '../ui'

const AUTOSAVE_MS = 900
// Narration the Claude Code agent writes lands via the API, so re-poll to show
// it live. Small payload; a few-second cadence is plenty.
const POLL_MS = 3000

// Step navigation lives in the wizard's left rail, so this step takes no goTo.
export default function NarrationStep({ project }) {
  const toast = useToast()

  const [slides, setSlides] = useState(null)
  const [current, setCurrent] = useState(0)
  const [error, setError] = useState('')
  const [saveState, setSaveState] = useState('idle')
  // What the last reattached PDF changed. Cleared server-side once no slide is
  // still flagged, so it disappears on its own as the slides get dealt with.
  const [review, setReview] = useState(null)

  const timers = useRef({})
  const pending = useRef({})
  const activeThumbRef = useRef(null)

  const imageByIndex = useMemo(() => {
    const m = {}
    ;(project.slides || []).forEach((s) => {
      m[s.index] = toRel(s.image_url)
    })
    return m
  }, [project.slides])

  const loadNarration = useCallback(async () => {
    const data = await api.getNarration(project.id)
    setReview(data.review?.total ? data.review : null)
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

  // On unmount, cancel pending autosave timers — but fire their saves first.
  // Leaving Narration is now done from the step rail (outside this component),
  // so a still-unsaved edit must not be dropped just because the step changed.
  // Calls the API directly rather than flush(), which would setState on an
  // unmounted component.
  useEffect(() => {
    const pendingRef = pending.current
    const timersRef = timers.current
    return () => {
      Object.values(timersRef).forEach(clearTimeout)
      Object.entries(pendingRef).forEach(([index, text]) => {
        api.saveNarration(project.id, Number(index), text).catch(() => {})
      })
    }
  }, [project.id])

  // Keep the selected thumbnail visible in the strip. `block: 'nearest'` so this
  // never scrolls the page itself, only the strip.
  useEffect(() => {
    activeThumbRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest',
      inline: 'center',
    })
  }, [current])

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

  // Waving a slide through: its narration still fits the edited slide, so drop
  // the flag without touching the text (and without re-synthesizing its audio).
  const keepAsIs = useCallback(
    async (index) => {
      try {
        await api.clearReview(project.id, [index])
        setSlides((prev) =>
          prev.map((s) => (s.index === index ? { ...s, change: null } : s))
        )
      } catch (err) {
        toast.error(err.message)
      }
    },
    [project.id, toast]
  )

  const clearAll = useCallback(async () => {
    try {
      await api.clearReview(project.id)
      setSlides((prev) => prev.map((s) => ({ ...s, change: null })))
      setReview(null)
    } catch (err) {
      toast.error(err.message)
    }
  }, [project.id, toast])

  const onEdit = (index, text) => {
    setSlides((prev) =>
      // Editing a flagged slide is exactly what the flag was asking for; the
      // backend drops it on save, so drop it here too rather than let the poll
      // blink it away a few seconds later.
      prev.map((s) =>
        s.index === index ? { ...s, narration: text, change: null } : s
      )
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
  const flagged = slides.filter((s) => s.change)
  const slideChange = CHANGE_LABELS[slide?.change]

  return (
    <div className="animate-fadein">
      <StepHeader
        step="2 · Narration"
        title="Narration"
        subtitle="You can edit the narration by hand in the right pane or ask Claude to make edits. Changes autosave."
        right={<SaveIndicator state={saveState} />}
      />

      {review && (
        <div className="mb-3">
          <ReviewSummary review={review}>
            <div className="flex flex-shrink-0 gap-2">
              {flagged.length > 0 && (
                <Button
                  variant="subtle"
                  size="sm"
                  onClick={() => goToIndex(slides.indexOf(flagged[0]))}
                >
                  Go to first flagged
                </Button>
              )}
              <Button variant="ghost" size="sm" onClick={clearAll}>
                Dismiss
              </Button>
            </div>
          </ReviewSummary>
        </div>
      )}

      {/* Thumbnail strip across the top, so the preview and editor below get the
          full width. Horizontal scroll keeps it one row however long the deck is;
          the active thumb is scrolled into view when you page with Previous/Next. */}
      <div className="scroll-thin mb-3 flex gap-2 overflow-x-auto rounded-xl border border-slate-200/60 bg-white p-2 shadow-sm">
        {slides.map((s, i) => {
          const est = estimateSeconds(s.narration)
          const empty = !s.narration?.trim()
          const active = i === current
          const change = CHANGE_LABELS[s.change]
          return (
            <button
              key={s.index}
              ref={active ? activeThumbRef : null}
              onClick={() => goToIndex(i)}
              title={`${i + 1}. ${s.title || `Slide ${i + 1}`} — ${
                empty ? 'no narration' : `~${est.seconds}s`
              }${change ? ` · ${change.label} in the reattached deck` : ''}`}
              className={`group relative aspect-video w-[104px] flex-shrink-0 overflow-hidden rounded-lg border-2 transition ${
                active
                  ? 'border-brand-600 ring-2 ring-brand-500/20'
                  : 'border-line hover:border-slate-300'
              }`}
            >
              {imageByIndex[s.index] ? (
                <img
                  src={imageByIndex[s.index]}
                  alt=""
                  loading="lazy"
                  className="h-full w-full object-cover"
                />
              ) : (
                <span className="flex h-full w-full items-center justify-center bg-slate-50 text-xs text-muted">
                  {i + 1}
                </span>
              )}
              <span
                className={`absolute bottom-0 left-0 rounded-tr-md px-1.5 py-0.5 text-[0.65rem] font-bold tabular-nums ${
                  active ? 'bg-brand-600 text-white' : 'bg-white/85 text-slate'
                }`}
              >
                {i + 1}
              </span>
              {empty && (
                <span
                  className="absolute right-1 top-1 h-2 w-2 rounded-full bg-amber-500 ring-1 ring-white"
                  aria-label="No narration"
                />
              )}
              {change && (
                <span
                  className={`absolute left-0 top-0 rounded-br-md px-1.5 py-0.5 text-[0.6rem] font-bold uppercase tracking-wide text-white ${change.dot}`}
                >
                  {change.label}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Preview · editor, side by side under the strip */}
      <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        {/* Slide preview */}
        <div className="flex h-[60vh] flex-col rounded-xl border border-slate-200/60 bg-white p-3 shadow-sm">
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
        <div className="flex h-[60vh] flex-col">
          <div className="mb-1.5 flex items-baseline justify-between">
            <span className="text-sm font-semibold text-navy">Narration</span>
            <span className="text-xs text-muted tabular-nums">
              {words} words · ~{seconds} sec
            </span>
          </div>
          {slideChange && (
            <div className="mb-1.5 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-brand-200 bg-brand-50/60 px-3 py-2 text-xs">
              <span className="text-slate">
                {slide.change === 'new'
                  ? 'This slide is new in the reattached deck — it has no narration yet.'
                  : 'This slide changed in the reattached deck. The script below is the one it had before.'}
              </span>
              <Button
                variant="subtle"
                size="sm"
                onClick={() => keepAsIs(slide.index)}
              >
                <Check className="h-3.5 w-3.5" /> Keep as is
              </Button>
            </div>
          )}
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

import { useEffect, useMemo, useRef, useState } from 'react'
import { ArrowLeft, ArrowRight, Film, Image as ImageIcon } from 'lucide-react'
import { toRel, videoUrl } from '../api'
import { estimateSeconds, formatDuration } from '../constants'
import AudioPanel from './AudioPanel'

// The whole app: thumbnails across the top, the slide (or the finished video) on
// the left, that slide's speaker notes on the right, and the audio controls
// underneath. One screen, because there is nowhere else to go — the notes are
// edited in the deck itself, not here.
export default function DeckView({ project, refresh }) {
  const slides = project.slides || []
  const [current, setCurrent] = useState(0)
  const [pane, setPane] = useState('slide')
  const activeThumbRef = useRef(null)

  const built = project.state === 'built'

  // A deck that shrank on reload can leave the selection past the end.
  useEffect(() => {
    if (current > slides.length - 1) setCurrent(Math.max(0, slides.length - 1))
  }, [slides.length, current])

  // Keep the selected thumbnail visible. `block: 'nearest'` so this never
  // scrolls the page itself, only the strip.
  useEffect(() => {
    activeThumbRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest',
      inline: 'center',
    })
  }, [current])

  useEffect(() => {
    if (!built && pane === 'video') setPane('slide')
  }, [built, pane])

  const totals = useMemo(() => {
    let words = 0
    let seconds = 0
    let empty = 0
    slides.forEach((s) => {
      const est = estimateSeconds(s.notes)
      words += est.words
      seconds += est.seconds
      if (!s.notes?.trim()) empty += 1
    })
    return { words, seconds, empty }
  }, [slides])

  if (!slides.length) return null

  const slide = slides[Math.min(current, slides.length - 1)]
  const { words, seconds } = estimateSeconds(slide?.notes)

  const go = (i) => setCurrent(Math.max(0, Math.min(slides.length - 1, i)))

  return (
    <div className="animate-fadein space-y-3">
      {/* Thumbnail strip. Horizontal scroll keeps it one row however long the
          deck is; the active thumb is scrolled into view when you page. */}
      <div className="scroll-thin flex gap-2 overflow-x-auto rounded-xl border border-slate-200/60 bg-white p-2 shadow-sm">
        {slides.map((s, i) => {
          const est = estimateSeconds(s.notes)
          const empty = !s.notes?.trim()
          const active = i === current
          return (
            <button
              key={s.index}
              ref={active ? activeThumbRef : null}
              onClick={() => go(i)}
              title={`${i + 1}. ${s.title || `Slide ${i + 1}`} — ${
                empty ? 'no speaker notes' : `~${est.seconds}s`
              }`}
              className={`group relative aspect-video w-[104px] flex-shrink-0 overflow-hidden rounded-lg border-2 transition ${
                active
                  ? 'border-brand-600 ring-2 ring-brand-500/20'
                  : 'border-line hover:border-slate-300'
              }`}
            >
              {s.image_url ? (
                <img
                  src={toRel(s.image_url)}
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
                  aria-label="No speaker notes"
                />
              )}
            </button>
          )
        })}
      </div>

      {/* Slide (or video) · notes, side by side under the strip */}
      <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div className="flex h-[58vh] flex-col rounded-xl border border-slate-200/60 bg-white p-3 shadow-sm">
          <div className="mb-2 flex items-center gap-1">
            <PaneTab
              active={pane === 'slide'}
              onClick={() => setPane('slide')}
              icon={ImageIcon}
              label="Slide"
            />
            <PaneTab
              active={pane === 'video'}
              onClick={() => built && setPane('video')}
              icon={Film}
              label="Video"
              disabled={!built}
              title={built ? '' : 'Generate the video first'}
            />
          </div>
          <div className="flex flex-1 items-center justify-center overflow-hidden rounded-lg bg-slate-50">
            {pane === 'video' ? (
              <video
                key={project.updated_at}
                src={`${videoUrl(project.id)}?v=${project.updated_at || 0}`}
                controls
                className="h-full w-full bg-black"
              />
            ) : slide?.image_url ? (
              <img
                src={toRel(slide.image_url)}
                alt={`Slide ${current + 1}`}
                className="max-h-full max-w-full object-contain"
              />
            ) : (
              <div className="text-muted">Slide {current + 1}</div>
            )}
          </div>
          {pane === 'slide' && (
            <div className="mt-2 flex items-center justify-between px-1 text-xs text-muted">
              <span>
                Slide {current + 1} of {slides.length}
              </span>
              <span className="truncate pl-2 font-medium text-slate">
                {slide?.title}
              </span>
            </div>
          )}
        </div>

        <div className="flex h-[58vh] flex-col">
          <div className="mb-1.5 flex items-baseline justify-between">
            <span className="text-sm font-semibold text-navy">
              Speaker notes
            </span>
            <span className="text-xs text-muted tabular-nums">
              {words} words · ~{seconds} sec
            </span>
          </div>
          <div className="scroll-thin flex-1 overflow-y-auto whitespace-pre-wrap rounded-xl border border-line bg-white p-4 text-sm leading-relaxed text-slate">
            {slide?.notes?.trim() || (
              <span className="text-muted">
                No speaker notes on this slide — it will be shown silently for a
                few seconds. Add notes in the deck (or ask Claude to draft them),
                then press Reload.
              </span>
            )}
          </div>
          <div className="mt-3 flex items-center justify-between">
            <button
              className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-white px-3 py-1.5 text-xs font-semibold text-slate transition hover:bg-slate-50 disabled:opacity-40"
              disabled={current === 0}
              onClick={() => go(current - 1)}
            >
              <ArrowLeft className="h-4 w-4" /> Previous
            </button>
            <span className="text-xs text-muted">
              {slides.length - totals.empty} of {slides.length} narrated ·
              ~{formatDuration(totals.seconds)} total
            </span>
            <button
              className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-white px-3 py-1.5 text-xs font-semibold text-slate transition hover:bg-slate-50 disabled:opacity-40"
              disabled={current === slides.length - 1}
              onClick={() => go(current + 1)}
            >
              Next <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      <AudioPanel
        project={project}
        refresh={refresh}
        onBuilt={() => setPane('video')}
      />
    </div>
  )
}

function PaneTab({ active, onClick, icon: Icon, label, disabled, title }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
        active
          ? 'bg-brand-tint text-brand-700'
          : disabled
            ? 'cursor-not-allowed text-muted opacity-50'
            : 'text-muted hover:bg-slate-50'
      }`}
    >
      <Icon className="h-3.5 w-3.5" /> {label}
    </button>
  )
}

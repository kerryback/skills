import { useEffect, useRef, useState } from 'react'
import { Loader2, ArrowRight } from 'lucide-react'
import { toRel } from '../../api'
import { JOB_TERMINALS } from '../../constants'
import { useJobEvents } from '../../hooks/useJobEvents'
import { useToast } from '../Toast'
import {
  Button,
  Card,
  StepHeader,
  ProgressBar,
  ErrorBanner,
} from '../ui'

export default function UploadStep({ project, refresh, goTo }) {
  const { progress, running, start } = useJobEvents()
  const toast = useToast()
  const [failLog, setFailLog] = useState('')
  const watched = useRef(false)

  const converting =
    project.state === 'converting' || project.state === 'uploaded'
  const converted =
    project.state !== 'uploaded' &&
    project.state !== 'converting' &&
    project.state !== 'converting_failed'

  // Watch the conversion job once when the project is still converting.
  useEffect(() => {
    if (!converting || watched.current) return
    watched.current = true
    start(project.id, {
      terminals: JOB_TERMINALS.convert,
      onDone: async () => {
        toast.success('Slides converted.')
        await refresh()
        goTo('narration')
      },
      onError: (err, evt) => {
        setFailLog(evt?.message || err.message)
        toast.error('Conversion failed.')
        refresh()
      },
    })
  }, [converting, project.id, start, refresh, goTo, toast])

  const slides = project.slides || []

  return (
    <div className="animate-fadein">
      <StepHeader
        step="1 · Upload"
        title="Upload & convert"
        subtitle="Your deck is converted into per-slide images. This runs automatically after upload."
      />

      {project.state === 'converting_failed' && (
        <div className="space-y-3">
          <ErrorBanner message="The deck could not be converted." />
          {(failLog || project.log) && (
            <LogBox log={failLog || project.log} />
          )}
          <p className="text-sm text-muted">
            Check the file format and create a new voiceover to try again.
          </p>
        </div>
      )}

      {converting && (
        <Card className="p-6">
          <div className="mb-4 flex items-center gap-3">
            <Loader2 className="h-6 w-6 animate-spin text-brand-600" />
            <div>
              <p className="font-semibold text-navy">Converting your deck…</p>
              <p className="text-sm text-muted">
                Rendering each slide to an image. This can take a moment.
              </p>
            </div>
          </div>
          <ProgressBar progress={progress} />
        </Card>
      )}

      {converted && (
        <div className="space-y-5">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate">
              {slides.length} slide{slides.length === 1 ? '' : 's'} ready
            </p>
            <Button onClick={() => goTo('narration')}>
              Continue to Draft <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
          <ThumbnailStrip project={project} slides={slides} />
        </div>
      )}

      {!converting && !converted && project.state !== 'converting_failed' && (
        <Card className="p-6">
          <ProgressBar progress={progress} />
        </Card>
      )}
    </div>
  )
}

function ThumbnailStrip({ slides }) {
  if (!slides.length) return null
  return (
    <div className="scroll-thin grid max-h-[60vh] grid-cols-2 gap-3 overflow-y-auto sm:grid-cols-3 lg:grid-cols-4">
      {slides.map((s) => (
        <figure
          key={s.index}
          className="overflow-hidden rounded-lg border border-slate-200/60 bg-white shadow-sm"
        >
          <img
            src={toRel(s.image_url)}
            alt={`Slide ${s.index + 1}`}
            loading="lazy"
            className="aspect-video w-full object-cover"
          />
          <figcaption className="border-t border-line px-2 py-1 text-[0.7rem] text-muted">
            Slide {s.index + 1}
          </figcaption>
        </figure>
      ))}
    </div>
  )
}

function LogBox({ log }) {
  return (
    <pre className="scroll-thin max-h-52 overflow-auto rounded-lg border border-line bg-slate-900 p-3 text-xs leading-relaxed text-slate-100">
      {log}
    </pre>
  )
}

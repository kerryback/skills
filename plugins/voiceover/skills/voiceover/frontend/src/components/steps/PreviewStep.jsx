import { useState } from 'react'
import { RotateCw, ArrowLeft, AlertTriangle, CheckCircle2 } from 'lucide-react'
import { videoUrl } from '../../api'
import { Button, Card, StepHeader } from '../ui'

export default function PreviewStep({ project, goTo }) {
  const [nonce, setNonce] = useState(0)
  const src = `${videoUrl(project.id)}?v=${nonce}`

  return (
    <div className="animate-fadein">
      <StepHeader
        step="4 · Preview"
        title="Preview"
        subtitle="Watch the finished video. The MP4 and transcript have been saved to your working directory."
        right={
          <div className="flex flex-wrap gap-2">
            <Button variant="subtle" onClick={() => setNonce((n) => n + 1)}>
              <RotateCw className="h-4 w-4" /> Reload
            </Button>
            <Button variant="ghost" onClick={() => goTo('narration')}>
              <ArrowLeft className="h-4 w-4" /> Back to narration
            </Button>
            <Button variant="amber" onClick={() => goTo('generate')}>
              <RotateCw className="h-4 w-4" /> Regenerate
            </Button>
          </div>
        }
      />

      {project.stale ? (
        <div className="mb-3 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-700">
          <AlertTriangle className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
          <span>
            This video is from an earlier build. You&apos;ve edited the narration
            or settings since — regenerate to update it and re-save the files.
          </span>
        </div>
      ) : (
        <div className="mb-3 flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-2.5 text-sm text-green-700">
          <CheckCircle2 className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
          <span>
            Saved <code>{'<name>'}.mp4</code> and <code>{'<name>'}.txt</code> to
            your working directory. Regenerate to overwrite them with your latest
            edits.
          </span>
        </div>
      )}

      <Card className="overflow-hidden p-0">
        <video
          key={nonce}
          src={src}
          controls
          className="h-[72vh] w-full bg-black"
        />
      </Card>
    </div>
  )
}

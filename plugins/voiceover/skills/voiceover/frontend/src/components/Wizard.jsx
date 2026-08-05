import { useCallback, useEffect, useState } from 'react'
import { ArrowRight } from 'lucide-react'
import { api } from '../api'
import { STEPS, STATE_TO_STEP } from '../constants'
import { Button, Spinner, StatePill, ErrorBanner } from './ui'
import { useToast } from './Toast'
import StepTracker from './StepTracker'
import UploadStep from './steps/UploadStep'
import NarrationStep from './steps/NarrationStep'
import GenerateStep from './steps/GenerateStep'
import PreviewStep from './steps/PreviewStep'

// Highest step index reachable for a given persisted state.
// Steps: 0 upload · 1 narration · 2 generate · 3 preview.
// Once a deck is converted, narration and generate are both open — narration is
// authored by the Claude Code agent (and editable in place), with no separate
// drafting job to wait on.
const MAX_REACHABLE = {
  uploaded: 0,
  converting: 0,
  converting_failed: 0,
  converted: 2,
  building: 2,
  building_failed: 2,
  built: 4,
}

const stepIndex = (key) => STEPS.findIndex((s) => s.key === key)

export default function Wizard({ projectId, onBack, onSessionExpired }) {
  const [project, setProject] = useState(null)
  const [error, setError] = useState('')
  const [active, setActive] = useState(null)
  const toast = useToast()

  const refresh = useCallback(async () => {
    try {
      const p = await api.getProject(projectId)
      setProject(p)
      setError('')
      return p
    } catch (err) {
      if (err.status === 401) return onSessionExpired()
      setError(err.message)
      return null
    }
  }, [projectId, onSessionExpired])

  // Initial load — land on the step matching the project's state.
  useEffect(() => {
    let cancelled = false
    api
      .getProject(projectId)
      .then((p) => {
        if (cancelled) return
        setProject(p)
        setActive(STATE_TO_STEP[p.state] || 'upload')
      })
      .catch((err) => {
        if (cancelled) return
        if (err.status === 401) onSessionExpired()
        else setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [projectId, onSessionExpired])

  if (error && !project) {
    return (
      <div className="mx-auto max-w-3xl px-5 py-10">
        <ErrorBanner message={error} onRetry={refresh} />
      </div>
    )
  }

  if (!project || !active) {
    return (
      <div className="flex items-center justify-center py-24 text-muted">
        <Spinner className="h-6 w-6 text-brand-blue" />
      </div>
    )
  }

  const naturalIdx = stepIndex(STATE_TO_STEP[project.state] || 'upload')
  const maxReach = MAX_REACHABLE[project.state] ?? 0

  const goTo = (key) => {
    const idx = stepIndex(key)
    if (idx <= maxReach) setActive(key)
    else toast.info('Finish the earlier steps first.')
  }

  const stepProps = {
    project,
    refresh,
    goTo,
    onSessionExpired,
  }

  return (
    <div className="mx-auto flex max-w-[1600px] flex-col gap-4 px-5 py-8 lg:flex-row lg:gap-5">
      {/* Narrow step rail — the wizard steps need very little width, and the
          Narration/Generate panes benefit from everything it gives back. */}
      <aside className="lg:w-44 lg:flex-shrink-0">
        <div className="lg:sticky lg:top-20">
          <div className="mb-4">
            <h2 className="truncate text-base font-extrabold tracking-tight text-navy">
              {project.name}
            </h2>
            <div className="mt-1.5">
              <StatePill state={project.state} stale={project.stale} />
            </div>
          </div>
          <StepTracker
            active={active}
            naturalIdx={naturalIdx}
            maxReach={maxReach}
            onSelect={goTo}
          />

          {/* Advance-to-Generate lives here rather than above the narration
              editor, where it read as an instruction to generate before writing
              anything. NarrationStep flushes unsaved edits on unmount, so
              leaving from the rail is safe. */}
          {active === 'narration' && stepIndex('generate') <= maxReach && (
            <Button
              className="mt-4 w-full"
              onClick={() => goTo('generate')}
            >
              Continue to Generate <ArrowRight className="h-4 w-4 flex-shrink-0" />
            </Button>
          )}
        </div>
      </aside>

      <section className="min-w-0 flex-1">
        {active === 'upload' && <UploadStep {...stepProps} />}
        {active === 'narration' && <NarrationStep {...stepProps} />}
        {active === 'generate' && <GenerateStep {...stepProps} />}
        {active === 'preview' && <PreviewStep {...stepProps} />}
      </section>
    </div>
  )
}

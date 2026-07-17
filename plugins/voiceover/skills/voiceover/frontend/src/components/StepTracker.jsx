import { Check } from 'lucide-react'
import { STEPS } from '../constants'

export default function StepTracker({ active, naturalIdx, maxReach, onSelect }) {
  return (
    <nav aria-label="Wizard steps">
      <ol className="relative space-y-1">
        {STEPS.map((step, i) => {
          const isActive = step.key === active
          const isComplete = i < naturalIdx
          const reachable = i <= maxReach
          const isLast = i === STEPS.length - 1

          return (
            <li key={step.key} className="relative">
              {!isLast && (
                <span
                  className={`absolute left-[1.15rem] top-9 h-[calc(100%-1rem)] w-px ${
                    i < naturalIdx ? 'bg-brand-600/40' : 'bg-line'
                  }`}
                  aria-hidden="true"
                />
              )}
              <button
                onClick={() => reachable && onSelect(step.key)}
                disabled={!reachable}
                aria-current={isActive ? 'step' : undefined}
                className={`group flex w-full items-center gap-3 rounded-xl px-2.5 py-2 text-left transition-colors ${
                  isActive
                    ? 'bg-brand-tint'
                    : reachable
                      ? 'hover:bg-slate-50'
                      : 'cursor-not-allowed opacity-55'
                }`}
              >
                <span
                  className={`relative z-10 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full border text-sm font-bold transition-colors ${
                    isComplete
                      ? 'border-brand-600 bg-brand-600 text-white'
                      : isActive
                        ? 'border-brand-600 bg-white text-brand-700'
                        : 'border-line bg-white text-muted'
                  }`}
                >
                  {isComplete ? (
                    <Check className="h-4 w-4" strokeWidth={3} />
                  ) : (
                    i + 1
                  )}
                </span>
                <span className="min-w-0">
                  <span
                    className={`block text-sm font-semibold ${
                      isActive
                        ? 'text-navy'
                        : reachable
                          ? 'text-slate'
                          : 'text-muted'
                    }`}
                  >
                    {step.label}
                  </span>
                  <span className="block text-[0.7rem] text-muted">
                    Step {i + 1}
                  </span>
                </span>
              </button>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}

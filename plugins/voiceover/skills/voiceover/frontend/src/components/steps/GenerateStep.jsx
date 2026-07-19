import { useState, useEffect } from 'react'
import {
  Headphones,
  RotateCw,
  ChevronDown,
  ArrowRight,
} from 'lucide-react'
import { api } from '../../api'
import {
  ELEVEN_MODELS,
  DEFAULT_TTS,
  JOB_TERMINALS,
} from '../../constants'
import { useJobEvents } from '../../hooks/useJobEvents'
import { useToast } from '../Toast'
import {
  Button,
  Card,
  Field,
  inputClass,
  StepHeader,
  ProgressBar,
  SlideTicks,
  ErrorBanner,
} from '../ui'

export default function GenerateStep({ project, refresh, goTo }) {
  const cfg = project.config || {}
  const [voiceId, setVoiceId] = useState(cfg.voice_id || DEFAULT_TTS.voice_id)
  const [model, setModel] = useState(cfg.model || DEFAULT_TTS.model)
  const [stability, setStability] = useState(
    cfg.stability ?? DEFAULT_TTS.stability
  )
  const [similarity, setSimilarity] = useState(
    cfg.similarity_boost ?? DEFAULT_TTS.similarity_boost
  )
  const [password, setPassword] = useState(cfg.password || '')

  const [voices, setVoices] = useState([])
  const [voicesConfigured, setVoicesConfigured] = useState(true)

  const [savedSnapshot, setSavedSnapshot] = useState(() =>
    JSON.stringify({
      voice_id: cfg.voice_id || DEFAULT_TTS.voice_id,
      model: cfg.model || DEFAULT_TTS.model,
      stability: cfg.stability ?? DEFAULT_TTS.stability,
      similarity_boost: cfg.similarity_boost ?? DEFAULT_TTS.similarity_boost,
    })
  )
  const [error, setError] = useState('')

  const { progress, running, start } = useJobEvents()
  const toast = useToast()

  // Fetch the account's ElevenLabs voices (includes cloned voices).
  useEffect(() => {
    let alive = true
    api
      .listVoices()
      .then((res) => {
        if (!alive) return
        setVoicesConfigured(res.configured)
        setVoices(res.voices || [])
      })
      .catch(() => {
        if (alive) setVoicesConfigured(true) // don't block on a transient error
      })
    return () => {
      alive = false
    }
  }, [])

  const config = {
    voice_id: voiceId,
    model,
    stability: Number(stability),
    similarity_boost: Number(similarity),
  }
  const dirty = JSON.stringify(config) !== savedSnapshot

  const saveConfig = async () => {
    try {
      await api.saveConfig(project.id, config)
      setSavedSnapshot(JSON.stringify(config))
    } catch (err) {
      toast.error(err.message)
      throw err
    }
  }

  const generate = async () => {
    setError('')
    if (!voicesConfigured) {
      setError(
        'Add your ElevenLabs API key (banner at the top of the page) before generating.'
      )
      return
    }
    if (!password.trim()) {
      setError('Set a password viewers will use before generating.')
      return
    }
    try {
      if (dirty) await saveConfig()
      await api.build(project.id)
      start(project.id, {
        terminals: JOB_TERMINALS.build,
        onDone: async () => {
          toast.success('Voiceover generated.')
          await refresh()
          goTo('preview')
        },
        onError: (err, evt) => {
          setError(evt?.message || err.message)
          toast.error('Generation failed.')
          refresh()
        },
      })
    } catch (err) {
      if (err) setError(err.message || String(err))
    }
  }

  const total = project.slides?.length || progress?.total || 0
  const built = project.state === 'built'

  return (
    <div className="animate-fadein">
      <StepHeader
        step="4 · Generate"
        title="Generate voiceover"
        subtitle="Choose a voice and style, set the viewer password, then generate the audio and build the narrated deck."
      />

      <ErrorBanner message={error} />

      <div className="mt-3 grid gap-4 lg:grid-cols-2">
        <Card className="space-y-5 p-6">
          <Field label="Voice" hint="From your ElevenLabs account, including cloned voices">
            {voicesConfigured ? (
              <div className="relative">
                <select
                  className={`${inputClass} appearance-none pr-9`}
                  value={voiceId}
                  onChange={(e) => setVoiceId(e.target.value)}
                >
                  {/* Keep the current value selectable even if it isn't in the
                      fetched list (not loaded yet, or a premade voice usable by
                      ID that the account's voice list doesn't return). */}
                  {!voices.some((v) => v.voice_id === voiceId) && (
                    <option value={voiceId}>
                      {voices.length === 0 ? voiceId : `Current: ${voiceId}`}
                    </option>
                  )}
                  {voices.map((v) => (
                    <option key={v.voice_id} value={v.voice_id}>
                      {v.name}
                      {v.category === 'cloned' ? ' (cloned)' : ''}
                    </option>
                  ))}
                </select>
                <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
              </div>
            ) : (
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
                Add your ElevenLabs API key in the banner at the top of the page
                to load your account's voices.
              </div>
            )}
          </Field>

          <Field label="Model" hint="Quality vs. speed">
            <div className="relative">
              <select
                className={`${inputClass} appearance-none pr-9`}
                value={model}
                onChange={(e) => setModel(e.target.value)}
              >
                {ELEVEN_MODELS.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.label}
                  </option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
            </div>
          </Field>

          <Field label={`Stability — ${Number(stability).toFixed(2)}`} hint="Lower is more expressive, higher is more consistent">
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={stability}
              onChange={(e) => setStability(e.target.value)}
              className="w-full accent-brand-600"
            />
          </Field>

          <Field label={`Similarity boost — ${Number(similarity).toFixed(2)}`} hint="How closely to match the source voice">
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={similarity}
              onChange={(e) => setSimilarity(e.target.value)}
              className="w-full accent-brand-600"
            />
          </Field>

          <Field label="Password viewers will use">
            <input
              className={inputClass}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Set a password to gate the deck"
              autoComplete="off"
            />
          </Field>
        </Card>

        <Card className="flex flex-col p-6">
          <h3 className="text-sm font-bold text-navy">Build the narrated deck</h3>
          <p className="mt-1 text-sm text-muted">
            Renders the deck, then synthesizes narration audio for each slide.
            Only slides whose narration changed are re-synthesized.
          </p>

          {running ? (
            <div className="mt-6 space-y-4">
              <ProgressBar progress={progress} tone="amber" />
              <SlideTicks
                total={progress?.total || total}
                done={progress?.done || 0}
              />
              <p className="text-xs text-muted">
                Generating audio — this can take a couple of minutes for a long
                deck.
              </p>
            </div>
          ) : (
            <div className="mt-6 flex flex-1 flex-col justify-end gap-3">
              {built && (
                <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
                  {project.stale
                    ? 'Narration or settings changed since the last build — regenerate to update.'
                    : 'Already built. Regenerate to apply new settings.'}
                </div>
              )}
              <Button
                size="lg"
                variant={built ? 'amber' : 'primary'}
                onClick={generate}
                disabled={!voicesConfigured}
              >
                {built ? (
                  <>
                    <RotateCw className="h-4 w-4" /> Regenerate
                  </>
                ) : (
                  <>
                    <Headphones className="h-4 w-4" /> Generate voiceover
                  </>
                )}
              </Button>
              {built && (
                <Button variant="ghost" onClick={() => goTo('preview')}>
                  Skip to preview <ArrowRight className="h-4 w-4" />
                </Button>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}

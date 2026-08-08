import { useEffect, useState } from 'react'
import {
  ChevronDown,
  Headphones,
  RotateCw,
  SlidersHorizontal,
} from 'lucide-react'
import { api } from '../api'
import {
  DEFAULT_TTS,
  ELEVEN_MODELS,
  JOB_TERMINALS,
  SPEED_RANGE,
  V3_STABILITY_LEVELS,
  modelInfo,
} from '../constants'
import { useJobEvents } from '../hooks/useJobEvents'
import { useToast } from './Toast'
import {
  Button,
  Card,
  ErrorBanner,
  Field,
  ProgressBar,
  SlideTicks,
  inputClass,
} from './ui'

// Voice, read settings, and the Generate button. Everything past the voice and
// the model sits behind a disclosure: the defaults are right for narration, and
// a wall of sliders above the button reads as work to do before generating.
export default function AudioPanel({ project, refresh, onBuilt }) {
  const cfg = project.config || {}
  const [voiceId, setVoiceId] = useState(cfg.voice_id || DEFAULT_TTS.voice_id)
  const [model, setModel] = useState(cfg.model || DEFAULT_TTS.model)
  const [stability, setStability] = useState(
    cfg.stability ?? DEFAULT_TTS.stability
  )
  const [similarity, setSimilarity] = useState(
    cfg.similarity_boost ?? DEFAULT_TTS.similarity_boost
  )
  const [style, setStyle] = useState(cfg.style ?? DEFAULT_TTS.style)
  const [speakerBoost, setSpeakerBoost] = useState(
    cfg.use_speaker_boost ?? DEFAULT_TTS.use_speaker_boost
  )
  const [speed, setSpeed] = useState(cfg.speed ?? DEFAULT_TTS.speed)

  const [voices, setVoices] = useState([])
  const [voicesConfigured, setVoicesConfigured] = useState(true)
  const [showAdvanced, setShowAdvanced] = useState(false)

  // A voice pasted from the ElevenLabs Voice Library, resolved to its name so
  // the instructor can see what they pasted. `library` holds the resolved voice
  // once it is accepted; it is offered in the dropdown alongside the account's.
  const [libraryId, setLibraryId] = useState('')
  const [library, setLibrary] = useState(null)
  const [lookingUp, setLookingUp] = useState(false)
  const [lookupError, setLookupError] = useState('')
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

  // A voice saved on this deck that the account doesn't list is a library voice
  // chosen earlier. Resolve it so it reads as a name rather than a bare id.
  useEffect(() => {
    if (!voicesConfigured || voices.length === 0) return
    if (library?.voice_id === voiceId) return
    if (voices.some((v) => v.voice_id === voiceId)) return
    let alive = true
    api
      .getVoice(voiceId)
      .then((v) => alive && setLibrary(v))
      .catch(() => {
        /* leave it showing the raw id */
      })
    return () => {
      alive = false
    }
  }, [voicesConfigured, voices, voiceId, library])

  const lookUpLibraryVoice = async () => {
    const id = libraryId.trim()
    if (!id) return
    setLookingUp(true)
    setLookupError('')
    try {
      const v = await api.getVoice(id)
      setLibrary(v)
      setVoiceId(v.voice_id)
      setLibraryId('')
    } catch (err) {
      setLookupError(err.message || 'Could not look up that voice.')
    } finally {
      setLookingUp(false)
    }
  }

  const info = modelInfo(model)
  const settings = {
    voice_id: voiceId,
    model,
    stability: Number(stability),
    similarity_boost: Number(similarity),
    style: Number(style),
    use_speaker_boost: speakerBoost,
    speed: Number(speed),
  }

  const generate = async () => {
    setError('')
    if (!voicesConfigured) {
      setError(
        'Add your ElevenLabs API key (banner at the top of the page) before generating.'
      )
      return
    }
    try {
      await api.saveConfig(project.id, settings)
      await api.build(project.id)
      start(project.id, {
        terminals: JOB_TERMINALS.build,
        onDone: async () => {
          toast.success('Voiceover generated.')
          await refresh()
          onBuilt?.()
        },
        onError: (err, evt) => {
          setError(evt?.message || err.message)
          toast.error('Generation failed.')
          refresh()
        },
      })
    } catch (err) {
      setError(err.message || String(err))
    }
  }

  const total = project.slides?.length || progress?.total || 0
  const built = project.state === 'built'
  const blocked = project.state === 'loading' || project.state === 'load_failed'

  return (
    <Card className="p-4">
      <ErrorBanner message={error} />

      <div className="flex flex-wrap items-end gap-3">
        <div className="min-w-[14rem] flex-1">
          <Field label="Voice" hint="Your ElevenLabs account, cloned voices included">
            {voicesConfigured ? (
              <div className="relative">
                <select
                  className={`${inputClass} appearance-none pr-9`}
                  value={voiceId}
                  onChange={(e) => setVoiceId(e.target.value)}
                >
                  {/* Keep the current value selectable even if it isn't in the
                      fetched list (not loaded yet, or a premade voice usable by
                      ID that the account's voice list doesn't return). Once it
                      resolves against the Voice Library it shows as a name. */}
                  {!voices.some((v) => v.voice_id === voiceId) &&
                    (library?.voice_id === voiceId ? (
                      <option value={voiceId}>
                        {library.name} (Voice Library)
                      </option>
                    ) : (
                      <option value={voiceId}>
                        {voices.length === 0 ? voiceId : `Current: ${voiceId}`}
                      </option>
                    ))}
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
        </div>

        <div className="min-w-[14rem] flex-1">
          <Field label="Model" hint="Expressiveness vs. speed">
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
        </div>

        <Button
          variant="subtle"
          onClick={() => setShowAdvanced((s) => !s)}
          aria-expanded={showAdvanced}
        >
          <SlidersHorizontal className="h-4 w-4" /> Read settings
        </Button>

        <Button
          size="lg"
          variant={built ? 'amber' : 'primary'}
          onClick={generate}
          loading={running}
          disabled={!voicesConfigured || blocked || running}
        >
          {built ? (
            <>
              <RotateCw className="h-4 w-4" /> Regenerate
            </>
          ) : (
            <>
              <Headphones className="h-4 w-4" /> Generate video
            </>
          )}
        </Button>
      </div>

      {running && (
        <div className="mt-4 space-y-3">
          <ProgressBar progress={progress} tone="amber" />
          <SlideTicks total={progress?.total || total} done={progress?.done || 0} />
          <p className="text-xs text-muted">
            Synthesizing the narration, then rendering the video — a couple of
            minutes for a long deck. Only notes that changed since the last run
            are re-synthesized.
          </p>
        </div>
      )}

      {!running && built && (
        <p className="mt-3 text-xs text-muted">
          {project.stale
            ? 'The notes or the voice settings have changed since this video was made — regenerate to update it.'
            : 'Saved to your project folder as an .mp4 and a .txt transcript.'}
        </p>
      )}

      {showAdvanced && (
        <div className="mt-4 grid gap-5 border-t border-line pt-4 lg:grid-cols-2">
          {/* The account lists ~20 premade voices plus your own clones. The rest
              of ElevenLabs' library — thousands of voices — is browsable only on
              their site, which is also where you can audition them. Paste the id
              of one here; text-to-speech takes a library voice directly, with no
              add-to-my-voices step. */}
          {voicesConfigured && (
            <Field label="Voice Library" hint="Paste an ID from elevenlabs.io">
              <div className="flex gap-2">
                <input
                  className={inputClass}
                  value={libraryId}
                  placeholder="e.g. 21m00Tcm4TlvDq8ikWAM"
                  onChange={(e) => {
                    setLibraryId(e.target.value)
                    setLookupError('')
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      lookUpLibraryVoice()
                    }
                  }}
                />
                <Button
                  variant="subtle"
                  onClick={lookUpLibraryVoice}
                  loading={lookingUp}
                  disabled={!libraryId.trim() || lookingUp}
                >
                  Use
                </Button>
              </div>
              {lookupError ? (
                <p className="mt-1.5 text-xs text-red-600">{lookupError}</p>
              ) : library && library.voice_id === voiceId ? (
                <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted">
                  <span className="font-semibold text-navy">{library.name}</span>
                  {library.labels?.length > 0 && (
                    <span>{library.labels.join(' · ')}</span>
                  )}
                  {library.preview_url && (
                    <audio
                      controls
                      src={library.preview_url}
                      className="h-7 max-w-[13rem]"
                    />
                  )}
                </div>
              ) : (
                <p className="mt-1.5 text-xs text-muted">
                  Browse and audition at elevenlabs.io/app/voice-library, then
                  copy the voice's ID.
                </p>
              )}
            </Field>
          )}

          {/* v3 defines three named stability levels; the v2 family takes a
              continuous dial. Showing a slider for v3 would imply precision the
              model does not have. */}
          {info.discreteStability ? (
            <Field label="Stability" hint="How much range the read is allowed">
              <div className="grid grid-cols-3 gap-2">
                {V3_STABILITY_LEVELS.map((lv) => {
                  const active = Number(stability) === lv.value
                  return (
                    <button
                      key={lv.label}
                      type="button"
                      title={lv.hint}
                      onClick={() => setStability(lv.value)}
                      className={`rounded-lg border px-2 py-2 text-xs font-semibold transition ${
                        active
                          ? 'border-brand-600 bg-brand-50 text-brand-700'
                          : 'border-slate-200 bg-white text-muted hover:border-slate-300'
                      }`}
                    >
                      {lv.label}
                    </button>
                  )
                })}
              </div>
              <p className="mt-1.5 text-xs text-muted">
                {V3_STABILITY_LEVELS.find((lv) => Number(stability) === lv.value)
                  ?.hint || 'Pick a level.'}
              </p>
            </Field>
          ) : (
            <Field
              label={`Stability — ${Number(stability).toFixed(2)}`}
              hint="Lower is more expressive, higher is more consistent"
            >
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
          )}

          <Field
            label={`Style — ${Number(style).toFixed(2)}`}
            hint="Emotional emphasis; 0 is a plain read"
          >
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={style}
              onChange={(e) => setStyle(e.target.value)}
              className="w-full accent-brand-600"
            />
          </Field>

          <Field
            label={`Speed — ${Number(speed).toFixed(2)}×`}
            hint="Below 1 is slower, above 1 is faster"
          >
            <input
              type="range"
              min={SPEED_RANGE.min}
              max={SPEED_RANGE.max}
              step={SPEED_RANGE.step}
              value={speed}
              onChange={(e) => setSpeed(e.target.value)}
              className="w-full accent-brand-600"
            />
          </Field>

          {/* "Source voice" used to read as something the instructor supplied.
              It is the recordings the voice itself was built from — your own
              samples for a cloned voice, ElevenLabs' originals for a premade
              one — so the label now says that, and says when to leave it be. */}
          <Field
            label={`Similarity boost — ${Number(similarity).toFixed(2)}`}
            hint="Matters mainly for cloned voices"
          >
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={similarity}
              onChange={(e) => setSimilarity(e.target.value)}
              className="w-full accent-brand-600"
            />
            <p className="mt-1.5 text-xs text-muted">
              How closely to copy the recordings this voice was built from. Higher
              tracks them more faithfully, including any noise in them. The default
              is fine for the built-in voices — this is not the flatness dial.
            </p>
          </Field>

          <label className="flex cursor-pointer items-start gap-2.5">
            <input
              type="checkbox"
              checked={speakerBoost}
              onChange={(e) => setSpeakerBoost(e.target.checked)}
              className="mt-0.5 h-4 w-4 accent-brand-600"
            />
            <span>
              <span className="block text-sm font-semibold text-navy">
                Speaker boost
              </span>
              <span className="block text-xs text-muted">
                Strengthens resemblance to the voice. Slightly slower to generate.
              </span>
            </span>
          </label>
        </div>
      )}
    </Card>
  )
}

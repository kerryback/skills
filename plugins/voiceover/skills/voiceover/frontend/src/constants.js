// Shared domain constants mirrored from CONTRACT.md.

// ElevenLabs TTS models. Voice IDs are fetched live from the account
// (GET /api/tts/voices), so cloned voices appear too.
//
// Ordered best-first. v3 is the expressive model and the right default for
// lecture narration: multilingual v2 is stable by design, which on long
// explanatory prose reads as flat. v2 is kept for the cases where that even,
// unsurprising delivery is actually what you want, and turbo/flash are the
// speed tiers. Labels say what each one sounds like, not just where it sits on
// a quality ladder — "highest quality" on v2 was actively misleading once v3
// shipped, because the flatness people complain about is a model choice.
export const ELEVEN_MODELS = [
  {
    id: 'eleven_v3',
    label: 'v3 — most expressive (recommended)',
    discreteStability: true,
  },
  {
    id: 'eleven_multilingual_v2',
    label: 'Multilingual v2 — even, understated',
    discreteStability: false,
  },
  {
    id: 'eleven_turbo_v2_5',
    label: 'Turbo v2.5 — faster, less nuance',
    discreteStability: false,
  },
  {
    id: 'eleven_flash_v2_5',
    label: 'Flash v2.5 — fastest, flattest',
    discreteStability: false,
  },
]

export const modelInfo = (id) =>
  ELEVEN_MODELS.find((m) => m.id === id) || ELEVEN_MODELS[0]

// v3 exposes stability as three named levels rather than a continuous dial.
// The API does not reject in-between values, but only these three are defined,
// so the picker offers exactly them instead of a slider that implies more
// precision than the model has.
export const V3_STABILITY_LEVELS = [
  { value: 0, label: 'Creative', hint: 'Most range, occasional odd emphasis' },
  { value: 0.5, label: 'Natural', hint: 'Balanced — best for narration' },
  { value: 1, label: 'Robust', hint: 'Most consistent, least expressive' },
]

export const DEFAULT_TTS = {
  voice_id: 'EXAVITQu4vr4xnSDxMaL', // ElevenLabs "Sarah"
  model: 'eleven_v3',
  stability: 0.5,
  similarity_boost: 0.75,
  style: 0,
  use_speaker_boost: true,
  speed: 1,
}

// Bounds for the expressive controls, mirrored in CONTRACT.md.
export const SPEED_RANGE = { min: 0.7, max: 1.2, step: 0.05 }

// Deck states. Loading reads the deck and its PDF; building makes the video.
export const STATE_LABELS = {
  loading: ['bg-blue-50 text-brand-dark', 'Reading the deck…'],
  ready: ['bg-slate-100 text-slate-600', 'Ready'],
  load_failed: ['bg-red-50 text-red-600', "Couldn't read the deck"],
  building: ['bg-blue-50 text-brand-dark', 'Generating…'],
  building_failed: ['bg-red-50 text-red-600', 'Generation failed'],
  built: ['bg-green-50 text-green-700', 'Video ready'],
}

// Terminal states per job stage: success and failure.
export const JOB_TERMINALS = {
  load: { success: 'ready', failure: 'load_failed' },
  build: { success: 'built', failure: 'building_failed' },
}

export const isFailedState = (state) =>
  typeof state === 'string' && state.endsWith('failed')

// Speaking rate assumption for the ~seconds estimate (words per minute).
export const WORDS_PER_MINUTE = 150

export const estimateSeconds = (text) => {
  const words = (text || '').trim().split(/\s+/).filter(Boolean).length
  return { words, seconds: Math.round((words / WORDS_PER_MINUTE) * 60) }
}

// "8 min 20 sec" from a count of seconds.
export const formatDuration = (seconds) => {
  const m = Math.floor(seconds / 60)
  const s = Math.round(seconds % 60)
  return m ? `${m} min ${s} sec` : `${s} sec`
}

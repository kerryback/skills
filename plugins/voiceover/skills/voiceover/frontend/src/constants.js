// Shared domain constants mirrored from CONTRACT.md.
import { Upload, PenLine, Headphones, Play } from 'lucide-react'

export const STEPS = [
  { key: 'upload', label: 'Upload', icon: Upload },
  { key: 'narration', label: 'Narration', icon: PenLine },
  { key: 'generate', label: 'Generate', icon: Headphones },
  { key: 'preview', label: 'Preview', icon: Play },
]

// ElevenLabs TTS models offered in the Generate step. Voice IDs are fetched
// live from the account (GET /api/tts/voices), so cloned voices appear too.
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

// Map a project's persisted state to the wizard step the user should land on.
export const STATE_TO_STEP = {
  uploaded: 'upload',
  converting: 'upload',
  converting_failed: 'upload',
  converted: 'narration',
  building: 'generate',
  building_failed: 'generate',
  built: 'preview',
}

// Terminal states per job stage: success and failure.
export const JOB_TERMINALS = {
  convert: { success: 'converted', failure: 'converting_failed' },
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

// Per-slide flags a reattached PDF leaves behind: the slide's content moved, so
// its narration is carried over but wants another look. `null` means untouched.
export const CHANGE_LABELS = {
  edited: { label: 'Edited', dot: 'bg-brand-600' },
  new: { label: 'New', dot: 'bg-violet-500' },
}

// "2 slides edited, 1 new, 1 removed" — what the last reattach did to the deck.
export const describeReview = (review) => {
  if (!review) return ''
  const parts = []
  if (review.edited) parts.push(`${review.edited} edited`)
  if (review.new) parts.push(`${review.new} new`)
  if (review.removed) parts.push(`${review.removed} removed`)
  if (!parts.length) return 'no slides changed'
  const n = review.edited + review.new
  return `${parts.join(', ')}${n ? ` of ${review.total} slides` : ''}`
}

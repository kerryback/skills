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
export const ELEVEN_MODELS = [
  { id: 'eleven_multilingual_v2', label: 'Multilingual v2 — highest quality' },
  { id: 'eleven_turbo_v2_5', label: 'Turbo v2.5 — balanced' },
  { id: 'eleven_flash_v2_5', label: 'Flash v2.5 — fastest' },
]

export const DEFAULT_TTS = {
  voice_id: 'EXAVITQu4vr4xnSDxMaL', // ElevenLabs "Sarah"
  model: 'eleven_multilingual_v2',
  stability: 0.5,
  similarity_boost: 0.75,
}

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

// Small API client. All paths are RELATIVE (no leading slash) so the SPA works
// behind a proxy / sub-path when served by FastAPI.

async function request(path, { method = 'GET', body, headers, raw } = {}) {
  const opts = { method, credentials: 'same-origin', headers: { ...headers } }
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  }
  const res = await fetch(path, opts)
  if (!res.ok) {
    let detail = res.statusText
    try {
      const data = await res.json()
      detail = data.detail || data.message || detail
    } catch {
      /* non-JSON error body */
    }
    const err = new Error(detail || `Request failed (${res.status})`)
    err.status = res.status
    throw err
  }
  if (raw) return res
  if (res.status === 204) return null
  const ct = res.headers.get('content-type') || ''
  return ct.includes('application/json') ? res.json() : res.text()
}

export const api = {
  // ---- decks ----
  listProjects: () => request('api/projects'),
  getProject: (id) => request(`api/projects/${id}`),
  // Re-read the deck source and its PDF from disk. This is the whole edit
  // cycle: edit the notes in Quarto/PowerPoint (or ask Claude to), then reload.
  reload: (id) => request(`api/projects/${id}/reload`, { method: 'POST' }),
  saveConfig: (id, config) =>
    request(`api/projects/${id}/config`, { method: 'PUT', body: config }),

  // ---- jobs ----
  build: (id) => request(`api/projects/${id}/build`, { method: 'POST' }),

  // ---- ElevenLabs voices (account + cloned) for the voice picker ----
  listVoices: () => request('api/tts/voices'),
  // Resolve a pasted Voice Library id to its name, labels and preview clip.
  // Works for any voice in the library, not only the account's own.
  getVoice: (voiceId) => request(`api/tts/voices/${encodeURIComponent(voiceId)}`),

  // ---- ElevenLabs API key (paste-in-app; validated + persisted server-side) ----
  ttsStatus: () => request('api/tts/status'),
  setTtsKey: (api_key) =>
    request('api/tts/key', { method: 'POST', body: { api_key } }),
}

// URL helpers (also relative)
export const videoUrl = (id) => `api/projects/${id}/video`
export const eventsUrl = (id) => `api/projects/${id}/events`

// Normalize a server-provided URL to a relative path (drop a leading slash) so
// it resolves correctly behind a sub-path.
export const toRel = (url) => (url ? url.replace(/^\//, '') : url)

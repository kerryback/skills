// Small API client. All paths are RELATIVE (no leading slash) so the SPA works
// behind a proxy / sub-path when served by FastAPI. Cookies carry the session.

async function request(path, { method = 'GET', body, headers, raw } = {}) {
  const opts = { method, credentials: 'same-origin', headers: { ...headers } }
  if (body instanceof FormData) {
    opts.body = body
  } else if (body !== undefined) {
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
  // ---- projects ----
  listProjects: () => request('api/projects'),
  getProject: (id) => request(`api/projects/${id}`),
  createProject: (name, file) => {
    const fd = new FormData()
    fd.append('name', name)
    fd.append('file', file)
    return request('api/projects', { method: 'POST', body: fd })
  },

  // ---- jobs ----
  build: (id) => request(`api/projects/${id}/build`, { method: 'POST' }),

  // ---- narration & config ----
  // Narration is written and revised by the Claude Code agent (bulk PUT); the
  // instructor can also hand-edit any slide (per-slide PUT autosave).
  getNarration: (id) => request(`api/projects/${id}/narration`),
  saveNarration: (id, index, narration) =>
    request(`api/projects/${id}/narration/${index}`, {
      method: 'PUT',
      body: { narration },
    }),
  saveNarrationBulk: (id, slides) =>
    request(`api/projects/${id}/narration`, { method: 'PUT', body: { slides } }),
  saveConfig: (id, config) =>
    request(`api/projects/${id}/config`, { method: 'PUT', body: config }),

  // ---- ElevenLabs voices (account + cloned) for the Generate picker ----
  listVoices: () => request('api/tts/voices'),

  // ---- ElevenLabs API key (paste-in-app; validated + persisted server-side) ----
  ttsStatus: () => request('api/tts/status'),
  setTtsKey: (api_key) =>
    request('api/tts/key', { method: 'POST', body: { api_key } }),
}

// URL helpers (also relative)
export const slideUrl = (id, file) => `api/projects/${id}/slides/${file}`
export const videoUrl = (id) => `api/projects/${id}/video`
export const eventsUrl = (id) => `api/projects/${id}/events`

// Normalize a server-provided URL to a relative path (drop a leading slash) so
// it resolves correctly behind a sub-path.
export const toRel = (url) => (url ? url.replace(/^\//, '') : url)

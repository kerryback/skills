import { useState } from 'react'
import { Headphones, ArrowLeft } from 'lucide-react'
import { ToastProvider } from './components/Toast'
import { Button } from './components/ui'
import ProjectsView from './components/ProjectsView'
import Wizard from './components/Wizard'
import ApiKeyBanner from './components/ApiKeyBanner'

// The skill launcher opens the app at /?project=<id>, so we deep-link straight
// into that project's wizard (landing on Narration once the deck has converted).
const initialProject = () =>
  new URLSearchParams(window.location.search).get('project') || null

function Shell() {
  const [openId, setOpenId] = useState(initialProject)
  const noop = () => {}

  return (
    <div className="min-h-full flex flex-col">
      <TopBar onHome={() => setOpenId(null)} inProject={openId != null} />
      <ApiKeyBanner />
      <main className="flex-1">
        {openId == null ? (
          <ProjectsView onOpen={(id) => setOpenId(id)} onSessionExpired={noop} />
        ) : (
          <Wizard
            projectId={openId}
            onBack={() => setOpenId(null)}
            onSessionExpired={noop}
          />
        )}
      </main>
    </div>
  )
}

function TopBar({ onHome, inProject }) {
  return (
    <header className="sticky top-0 z-30 border-b border-navy/40 bg-navy text-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3">
        <button
          onClick={onHome}
          className="flex items-center gap-2.5 text-left transition-opacity hover:opacity-90"
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10">
            <Headphones className="h-4 w-4" />
          </span>
          <span>
            <span className="block text-sm font-extrabold leading-tight tracking-tight">
              Voiceover Builder
            </span>
          </span>
        </button>
        <div className="flex items-center gap-2">
          {inProject && (
            <Button
              variant="ghost"
              size="sm"
              className="border-white/30 text-white hover:bg-white/10"
              onClick={onHome}
            >
              <ArrowLeft className="h-4 w-4" /> All projects
            </Button>
          )}
        </div>
      </div>
    </header>
  )
}

export default function App() {
  return (
    <ToastProvider>
      <Shell />
    </ToastProvider>
  )
}

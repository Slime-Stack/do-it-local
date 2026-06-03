import { useEffect, useRef, useState } from 'react'
import Home from './pages/Home'
import Pipeline from './pages/Pipeline'
import Results from './pages/Results'
import { handleOAuthCallback, hasPendingCallback } from './oauth'
import type { DoneEvent } from './types'

type View = 'home' | 'pipeline' | 'results'

interface PipelineInput {
  projectUrl: string
  gitlabPat: string
  mcpToken: string
  targetBranch: string
  environmentTarget: string
}

function App() {
  const [view, setView] = useState<View>('home')
  const [input, setInput] = useState<PipelineInput | null>(null)
  const [results, setResults] = useState<DoneEvent['results'] | null>(null)
  const [oauthError, setOauthError] = useState('')
  const oauthHandled = useRef(false)

  useEffect(() => {
    if (oauthHandled.current) return

    if (window.location.pathname === '/oauth/callback') {
      if (!hasPendingCallback()) {
        window.history.replaceState({}, '', '/')
        return
      }
    } else {
      return
    }

    oauthHandled.current = true
    handleOAuthCallback()
      .then(({ mcpToken, gitlabPat, projectUrl, targetBranch, environmentTarget }) => {
        window.history.replaceState({}, '', '/')
        setInput({ projectUrl, gitlabPat, mcpToken, targetBranch, environmentTarget })
        setView('pipeline')
      })
      .catch((err) => {
        window.history.replaceState({}, '', '/')
        setOauthError(err.message)
      })
  }, [])

  const handleComplete = (r: DoneEvent['results']) => {
    setResults(r)
    setView('results')
  }

  const handleReset = () => {
    setInput(null)
    setResults(null)
    setOauthError('')
    setView('home')
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800 px-6 py-4">
        <button onClick={handleReset} className="text-xl font-bold tracking-tight">
          Do It Local
        </button>
      </header>
      <main className="mx-auto max-w-4xl px-6 py-12">
        {view === 'home' && <Home oauthError={oauthError} />}
        {view === 'pipeline' && input && (
          <Pipeline
            projectUrl={input.projectUrl}
            gitlabPat={input.gitlabPat}
            mcpToken={input.mcpToken}
            targetBranch={input.targetBranch}
            environmentTarget={input.environmentTarget}
            onComplete={handleComplete}
          />
        )}
        {view === 'results' && results && (
          <Results results={results} onReset={handleReset} />
        )}
      </main>
    </div>
  )
}

export default App

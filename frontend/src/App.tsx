import { useState } from 'react'
import Home from './pages/Home'
import Pipeline from './pages/Pipeline'
import Results from './pages/Results'

type View = 'home' | 'pipeline' | 'results'

interface JobState {
  jobId: string
  projectUrl: string
}

function App() {
  const [view, setView] = useState<View>('home')
  const [job, setJob] = useState<JobState | null>(null)

  const handleJobCreated = (jobId: string, projectUrl: string) => {
    setJob({ jobId, projectUrl })
    setView('pipeline')
  }

  const handlePipelineComplete = () => {
    setView('results')
  }

  const handleReset = () => {
    setJob(null)
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
        {view === 'home' && <Home onJobCreated={handleJobCreated} />}
        {view === 'pipeline' && job && (
          <Pipeline jobId={job.jobId} onComplete={handlePipelineComplete} />
        )}
        {view === 'results' && job && (
          <Results jobId={job.jobId} onReset={handleReset} />
        )}
      </main>
    </div>
  )
}

export default App

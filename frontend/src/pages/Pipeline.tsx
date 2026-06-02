import { useEffect, useState } from 'react'
import { getJobStatus } from '../api/client'

interface PipelineProps {
  jobId: string
  onComplete: () => void
}

const STEPS = [
  { key: 'scanning', label: 'Scanner', description: 'Reading repo structure and dependencies' },
  { key: 'detecting', label: 'Detector', description: 'Identifying PII and side-effect services' },
  { key: 'generating', label: 'Generator', description: 'Creating docker-compose, .env, and seed scripts' },
]

export default function Pipeline({ jobId, onComplete }: PipelineProps) {
  const [status, setStatus] = useState('pending')
  const [error, setError] = useState('')

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const result = await getJobStatus(jobId)
        setStatus(result.status)

        if (result.status === 'complete') {
          clearInterval(interval)
          onComplete()
        } else if (result.status === 'error') {
          clearInterval(interval)
          setError(result.error || 'Pipeline failed')
        }
      } catch {
        clearInterval(interval)
        setError('Failed to poll job status')
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [jobId, onComplete])

  const getStepStatus = (stepKey: string) => {
    const stepOrder = ['scanning', 'detecting', 'generating']
    const currentIdx = stepOrder.indexOf(status)
    const stepIdx = stepOrder.indexOf(stepKey)

    if (status === 'complete') return 'complete'
    if (stepIdx < currentIdx) return 'complete'
    if (stepIdx === currentIdx) return 'active'
    return 'pending'
  }

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-bold text-center">Analyzing Repository</h2>

      <div className="space-y-4">
        {STEPS.map((step, i) => {
          const stepStatus = getStepStatus(step.key)
          return (
            <div
              key={step.key}
              className={`rounded-lg border p-4 transition-colors ${
                stepStatus === 'active'
                  ? 'border-blue-500 bg-blue-950/30'
                  : stepStatus === 'complete'
                  ? 'border-green-700 bg-green-950/20'
                  : 'border-gray-800 bg-gray-900/50'
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold ${
                    stepStatus === 'active'
                      ? 'bg-blue-600 text-white'
                      : stepStatus === 'complete'
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-800 text-gray-500'
                  }`}
                >
                  {stepStatus === 'complete' ? '\u2713' : i + 1}
                </div>
                <div>
                  <p className="font-semibold">{step.label}</p>
                  <p className="text-sm text-gray-400">{step.description}</p>
                </div>
                {stepStatus === 'active' && (
                  <div className="ml-auto h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
                )}
              </div>
            </div>
          )
        })}
      </div>

      {error && (
        <div className="rounded-lg border border-red-700 bg-red-950/30 p-4 text-red-300">
          {error}
        </div>
      )}
    </div>
  )
}

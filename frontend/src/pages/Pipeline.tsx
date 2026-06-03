import { useEffect, useRef, useState } from 'react'
import { streamPipeline } from '../api/client'
import type { DoneEvent, PipelineEvent } from '../types'

interface PipelineProps {
  projectUrl: string
  gitlabPat: string
  mcpToken: string
  targetBranch: string
  environmentTarget: string
  onComplete: (results: DoneEvent['results']) => void
}

interface ActivityItem {
  id: number
  agent: string
  type: string
  summary: string
}

const STEPS = [
  { key: 'scanning', label: 'Scanner', description: 'Reading repo structure and dependencies' },
  { key: 'detecting', label: 'Detector', description: 'Identifying PII and side-effect services' },
  { key: 'recommending', label: 'Recommender', description: 'Proposing environment strategy' },
  { key: 'generating', label: 'Generator', description: 'Creating configs and merge request' },
]

let nextId = 0

export default function Pipeline({ projectUrl, gitlabPat, mcpToken, targetBranch, environmentTarget, onComplete }: PipelineProps) {
  const [status, setStatus] = useState('scanning')
  const [activity, setActivity] = useState<ActivityItem[]>([])
  const [error, setError] = useState('')
  const feedRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const controller = new AbortController()

    const handleEvent = (event: PipelineEvent) => {
      if (event.type === 'status') {
        setStatus(event.status)
        return
      }

      if (event.type === 'done') {
        onComplete(event.results)
        return
      }

      if (event.type === 'error') {
        setError(event.error)
        return
      }

      let summary = ''
      const agent = 'agent' in event ? event.agent : ''

      if (event.type === 'tool_call') {
        const args = event.content.args
        const detail = args.file_path || args.path || args.branch_name || ''
        summary = `Calling ${event.content.name}${detail ? `: ${detail}` : ''}`
      } else if (event.type === 'tool_result') {
        summary = `${event.content.name} returned`
      } else if (event.type === 'text') {
        summary = event.content.length > 120 ? event.content.slice(0, 120) + '...' : event.content
      }

      if (summary) {
        setActivity((prev) => [...prev.slice(-49), { id: nextId++, agent, type: event.type, summary }])
      }
    }

    streamPipeline(projectUrl, gitlabPat, mcpToken, targetBranch, environmentTarget, handleEvent, controller.signal)
      .catch((err) => {
        if (err.name !== 'AbortError') {
          setError(err.message || 'Stream failed')
        }
      })

    return () => controller.abort()
  }, [projectUrl, gitlabPat, mcpToken, targetBranch, environmentTarget, onComplete])

  useEffect(() => {
    feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight, behavior: 'smooth' })
  }, [activity])

  const getStepStatus = (stepKey: string) => {
    const phases: Record<string, string> = {
      scanning: 'scanning',
      scanning_complete: 'detecting',
      detecting: 'detecting',
      detecting_complete: 'recommending',
      recommending: 'recommending',
      recommending_complete: 'generating',
      generating: 'generating',
      complete: 'complete',
    }
    const currentPhase = phases[status] || status
    const stepOrder = ['scanning', 'detecting', 'recommending', 'generating']
    const currentIdx = stepOrder.indexOf(currentPhase)
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

      {activity.length > 0 && (
        <div className="rounded-lg border border-gray-800 bg-gray-900/50">
          <div className="border-b border-gray-800 px-4 py-2">
            <p className="text-sm font-medium text-gray-400">Activity</p>
          </div>
          <div ref={feedRef} className="max-h-64 overflow-y-auto p-4 space-y-1">
            {activity.map((item) => (
              <div key={item.id} className="text-sm text-gray-300 font-mono">
                <span className="text-gray-500">{item.agent ? `[${item.agent}] ` : ''}</span>
                <span className={item.type === 'tool_call' ? 'text-blue-400' : item.type === 'tool_result' ? 'text-green-400' : ''}>
                  {item.summary}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-700 bg-red-950/30 p-4 text-red-300">
          {error}
        </div>
      )}
    </div>
  )
}

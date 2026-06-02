import { useEffect, useState } from 'react'
import { getJobResults } from '../api/client'

interface ResultsProps {
  jobId: string
  onReset: () => void
}

type Tab = 'scan' | 'detection' | 'generation'

export default function Results({ jobId, onReset }: ResultsProps) {
  const [results, setResults] = useState<Record<string, unknown> | null>(null)
  const [tab, setTab] = useState<Tab>('scan')
  const [error, setError] = useState('')

  useEffect(() => {
    getJobResults(jobId)
      .then(setResults)
      .catch(() => setError('Failed to load results'))
  }, [jobId])

  if (error) {
    return <div className="text-red-400">{error}</div>
  }

  if (!results) {
    return <div className="text-gray-400">Loading results...</div>
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: 'scan', label: 'Scan Summary' },
    { key: 'detection', label: 'Detection Report' },
    { key: 'generation', label: 'Generated Files' },
  ]

  const getContent = () => {
    switch (tab) {
      case 'scan':
        return results.scan_result
      case 'detection':
        return results.detection_result
      case 'generation':
        return results.generation_result
      default:
        return null
    }
  }

  const content = getContent()
  const mrUrl = (results.generation_result as Record<string, unknown>)?.merge_request_url as string | undefined

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Analysis Complete</h2>
        <button
          onClick={onReset}
          className="rounded-lg border border-gray-700 px-4 py-2 text-sm hover:bg-gray-800 transition-colors"
        >
          New Analysis
        </button>
      </div>

      {mrUrl && (
        <a
          href={mrUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="block rounded-lg border border-green-700 bg-green-950/20 p-4 text-green-300 hover:bg-green-950/40 transition-colors"
        >
          Merge Request Created &rarr;
        </a>
      )}

      <div className="flex gap-2 border-b border-gray-800">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              tab === t.key
                ? 'border-b-2 border-blue-500 text-blue-400'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <pre className="overflow-auto rounded-lg bg-gray-900 border border-gray-800 p-4 text-sm text-gray-300">
        {content ? JSON.stringify(content, null, 2) : 'No data available'}
      </pre>
    </div>
  )
}

import { useState } from 'react'
import type { DoneEvent } from '../types'

interface ResultsProps {
  results: DoneEvent['results']
  onReset: () => void
}

type Tab = 'scan' | 'detection' | 'recommendation' | 'generation'

const LANGUAGE_MAP: Record<string, string> = {
  'docker-compose.yml': 'yaml',
  'docker-compose.yaml': 'yaml',
  '.env.local': 'bash',
  'seed.sh': 'bash',
  'seed.py': 'python',
  'README.local.md': 'markdown',
}

function detectLanguage(filePath: string): string {
  for (const [pattern, lang] of Object.entries(LANGUAGE_MAP)) {
    if (filePath.endsWith(pattern)) return lang
  }
  if (filePath.endsWith('.yml') || filePath.endsWith('.yaml')) return 'yaml'
  if (filePath.endsWith('.py')) return 'python'
  if (filePath.endsWith('.sh')) return 'bash'
  if (filePath.endsWith('.md')) return 'markdown'
  return 'text'
}

export default function Results({ results, onReset }: ResultsProps) {
  const [tab, setTab] = useState<Tab>('scan')

  const tabs: { key: Tab; label: string }[] = [
    { key: 'scan', label: 'Scan Summary' },
    { key: 'detection', label: 'Detection Report' },
    { key: 'recommendation', label: 'Strategy' },
    { key: 'generation', label: 'Generated Files' },
  ]

  const getContent = () => {
    switch (tab) {
      case 'scan':
        return results.scan_result
      case 'detection':
        return results.detection_result
      case 'recommendation':
        return results.recommendation_result
      case 'generation':
        return results.generation_result
      default:
        return null
    }
  }

  const content = getContent()
  const mrUrl = (results.generation_result as Record<string, unknown>)?.merge_request_url as string | undefined
  const filesGenerated = (results.generation_result as Record<string, unknown>)?.files_generated as Array<Record<string, string>> | undefined

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
          className="block rounded-lg border border-green-700 bg-green-950/20 p-4 text-green-300 hover:bg-green-950/40 transition-colors text-center font-semibold"
        >
          View Merge Request on GitLab &rarr;
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

      {tab === 'generation' && filesGenerated ? (
        <div className="space-y-4">
          {filesGenerated.map((file) => (
            <div key={file.file_path} className="rounded-lg border border-gray-800 overflow-hidden">
              <div className="bg-gray-900 px-4 py-2 border-b border-gray-800 flex items-center justify-between">
                <span className="text-sm font-mono text-gray-300">{file.file_path}</span>
                <span className="text-xs text-gray-500">{detectLanguage(file.file_path)}</span>
              </div>
              <pre className="overflow-auto bg-gray-950 p-4 text-sm text-gray-300 max-h-96">
                <code>{file.content}</code>
              </pre>
            </div>
          ))}
        </div>
      ) : (
        <pre className="overflow-auto rounded-lg bg-gray-900 border border-gray-800 p-4 text-sm text-gray-300">
          {content ? JSON.stringify(content, null, 2) : 'No data available'}
        </pre>
      )}
    </div>
  )
}

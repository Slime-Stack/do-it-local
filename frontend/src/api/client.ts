import type { PipelineEvent } from '../types'

const API_KEY = import.meta.env.VITE_API_KEY || ''

export async function streamPipeline(
  projectUrl: string,
  gitlabPat: string,
  mcpToken: string,
  targetBranch: string,
  onEvent: (event: PipelineEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch('/api/pipeline/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
    },
    body: JSON.stringify({
      project_url: projectUrl,
      gitlab_token: gitlabPat,
      mcp_token: mcpToken,
      target_branch: targetBranch,
    }),
    signal,
  })

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`Pipeline request failed (${res.status}): ${text}`)
  }

  const reader = res.body?.getReader()
  if (!reader) throw new Error('No response body')

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed || trimmed.startsWith(':')) continue
      if (trimmed.startsWith('data: ')) {
        try {
          const event = JSON.parse(trimmed.slice(6)) as PipelineEvent
          onEvent(event)
        } catch {
          // skip malformed events
        }
      }
    }
  }
}

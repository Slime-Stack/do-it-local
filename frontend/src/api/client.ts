const API_KEY = import.meta.env.VITE_API_KEY || ''

const headers: Record<string, string> = {
  'Content-Type': 'application/json',
  'X-API-Key': API_KEY,
}

export async function createJob(projectUrl: string, gitlabToken: string, targetBranch = 'main') {
  const res = await fetch('/api/jobs', {
    method: 'POST',
    headers,
    body: JSON.stringify({
      project_url: projectUrl,
      gitlab_token: gitlabToken,
      target_branch: targetBranch,
    }),
  })
  if (!res.ok) throw new Error(`Failed to create job: ${res.status}`)
  return res.json()
}

export async function getJobStatus(jobId: string) {
  const res = await fetch(`/api/jobs/${jobId}`, { headers })
  if (!res.ok) throw new Error(`Failed to get status: ${res.status}`)
  return res.json()
}

export async function getJobResults(jobId: string) {
  const res = await fetch(`/api/jobs/${jobId}/results`, { headers })
  if (!res.ok) throw new Error(`Failed to get results: ${res.status}`)
  return res.json()
}

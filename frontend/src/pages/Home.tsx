import { useState } from 'react'
import { createJob } from '../api/client'

interface HomeProps {
  onJobCreated: (jobId: string, projectUrl: string) => void
}

export default function Home({ onJobCreated }: HomeProps) {
  const [projectUrl, setProjectUrl] = useState('')
  const [gitlabToken, setGitlabToken] = useState('')
  const [targetBranch, setTargetBranch] = useState('main')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const result = await createJob(projectUrl, gitlabToken, targetBranch)
      onJobCreated(result.job_id, projectUrl)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create job')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-5xl font-bold tracking-tight">
          Stop doing it live.
        </h1>
        <p className="text-xl text-gray-400">
          Analyze your codebase. Generate local dev configs. Delivered as a merge request.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="mx-auto max-w-lg space-y-4">
        <div>
          <label htmlFor="projectUrl" className="block text-sm font-medium text-gray-300 mb-1">
            GitLab Project URL
          </label>
          <input
            id="projectUrl"
            type="url"
            required
            placeholder="https://gitlab.com/your-group/your-project"
            value={projectUrl}
            onChange={(e) => setProjectUrl(e.target.value)}
            className="w-full rounded-lg bg-gray-900 border border-gray-700 px-4 py-3 text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none"
          />
        </div>

        <div>
          <label htmlFor="gitlabToken" className="block text-sm font-medium text-gray-300 mb-1">
            GitLab Personal Access Token
          </label>
          <input
            id="gitlabToken"
            type="password"
            required
            placeholder="glpat-..."
            value={gitlabToken}
            onChange={(e) => setGitlabToken(e.target.value)}
            className="w-full rounded-lg bg-gray-900 border border-gray-700 px-4 py-3 text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none"
          />
          <p className="mt-1 text-xs text-gray-500">Needs api scope. Never stored permanently.</p>
        </div>

        <div>
          <label htmlFor="targetBranch" className="block text-sm font-medium text-gray-300 mb-1">
            Target Branch
          </label>
          <input
            id="targetBranch"
            type="text"
            value={targetBranch}
            onChange={(e) => setTargetBranch(e.target.value)}
            className="w-full rounded-lg bg-gray-900 border border-gray-700 px-4 py-3 text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none"
          />
        </div>

        {error && (
          <p className="text-red-400 text-sm">{error}</p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Creating job...' : 'Analyze Repository'}
        </button>
      </form>
    </div>
  )
}

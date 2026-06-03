import { useState } from 'react'
import { startOAuthFlow } from '../oauth'

interface HomeProps {
  oauthError?: string
}

export default function Home({ oauthError }: HomeProps) {
  const [projectUrl, setProjectUrl] = useState('')
  const [gitlabPat, setGitlabPat] = useState('')
  const [targetBranch, setTargetBranch] = useState('main')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    startOAuthFlow(projectUrl, targetBranch, gitlabPat)
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
          <label htmlFor="gitlabPat" className="block text-sm font-medium text-gray-300 mb-1">
            GitLab Personal Access Token
          </label>
          <input
            id="gitlabPat"
            type="password"
            required
            placeholder="glpat-..."
            value={gitlabPat}
            onChange={(e) => setGitlabPat(e.target.value)}
            className="w-full rounded-lg bg-gray-900 border border-gray-700 px-4 py-3 text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none"
          />
          <p className="mt-1 text-xs text-gray-500">Needs api scope. Used for repo access. Never stored.</p>
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

        {oauthError && (
          <p className="text-red-400 text-sm">{oauthError}</p>
        )}

        <button
          type="submit"
          className="w-full rounded-lg bg-[#e24329] px-4 py-3 font-semibold text-white hover:bg-[#fc6d26] transition-colors flex items-center justify-center gap-2"
        >
          <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M23.955 13.587l-1.342-4.135-2.664-8.189a.455.455 0 00-.867 0L16.418 9.45H7.582L4.918 1.263a.455.455 0 00-.867 0L1.386 9.452.044 13.587a.924.924 0 00.331 1.023L12 23.054l11.625-8.443a.92.92 0 00.33-1.024" />
          </svg>
          Connect with GitLab &amp; Analyze
        </button>

        <p className="text-center text-xs text-gray-600">
          You'll authorize via GitLab OAuth for MCP access. Your PAT handles repo operations.
        </p>
      </form>
    </div>
  )
}

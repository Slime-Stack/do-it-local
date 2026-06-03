const GITLAB_CLIENT_ID = 'bfaa45b1f4b613d34f81dc0f948dd000c7abd1368adfcb4295ce316d8a94677f'
const GITLAB_URL = 'https://gitlab.com'
const REDIRECT_URI = `${window.location.origin}/oauth/callback`
const SCOPES = 'mcp'

function generateRandomString(length: number): string {
  const array = new Uint8Array(length)
  crypto.getRandomValues(array)
  return Array.from(array, (b) => b.toString(16).padStart(2, '0')).join('')
}

async function sha256(plain: string): Promise<ArrayBuffer> {
  const encoder = new TextEncoder()
  return crypto.subtle.digest('SHA-256', encoder.encode(plain))
}

function base64UrlEncode(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (const b of bytes) binary += String.fromCharCode(b)
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

export async function startOAuthFlow(
  projectUrl: string,
  targetBranch: string,
  gitlabPat: string,
): Promise<void> {
  const codeVerifier = generateRandomString(64)
  const codeChallenge = base64UrlEncode(await sha256(codeVerifier))
  const state = generateRandomString(32)

  sessionStorage.setItem('oauth_code_verifier', codeVerifier)
  sessionStorage.setItem('oauth_state', state)
  sessionStorage.setItem('oauth_project_url', projectUrl)
  sessionStorage.setItem('oauth_target_branch', targetBranch)
  sessionStorage.setItem('oauth_gitlab_pat', gitlabPat)

  const params = new URLSearchParams({
    client_id: GITLAB_CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    response_type: 'code',
    scope: SCOPES,
    state,
    code_challenge: codeChallenge,
    code_challenge_method: 'S256',
  })

  window.location.href = `${GITLAB_URL}/oauth/authorize?${params}`
}

export interface OAuthResult {
  mcpToken: string
  gitlabPat: string
  projectUrl: string
  targetBranch: string
}

export async function handleOAuthCallback(): Promise<OAuthResult> {
  const params = new URLSearchParams(window.location.search)
  const code = params.get('code')
  const state = params.get('state')
  const error = params.get('error')

  if (error) {
    throw new Error(`GitLab authorization failed: ${params.get('error_description') || error}`)
  }

  if (!code || !state) {
    throw new Error('Missing authorization code or state')
  }

  const savedState = sessionStorage.getItem('oauth_state')
  if (state !== savedState) {
    throw new Error('OAuth state mismatch — possible CSRF attack')
  }

  const codeVerifier = sessionStorage.getItem('oauth_code_verifier')
  if (!codeVerifier) {
    throw new Error('Missing code verifier — please restart the flow')
  }

  const projectUrl = sessionStorage.getItem('oauth_project_url') || ''
  const targetBranch = sessionStorage.getItem('oauth_target_branch') || 'main'
  const gitlabPat = sessionStorage.getItem('oauth_gitlab_pat') || ''

  const tokenRes = await fetch(`${GITLAB_URL}/oauth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: GITLAB_CLIENT_ID,
      code,
      grant_type: 'authorization_code',
      redirect_uri: REDIRECT_URI,
      code_verifier: codeVerifier,
    }),
  })

  if (!tokenRes.ok) {
    const text = await tokenRes.text().catch(() => tokenRes.statusText)
    throw new Error(`Token exchange failed (${tokenRes.status}): ${text}`)
  }

  const tokenData = await tokenRes.json()

  sessionStorage.removeItem('oauth_code_verifier')
  sessionStorage.removeItem('oauth_state')
  sessionStorage.removeItem('oauth_project_url')
  sessionStorage.removeItem('oauth_target_branch')
  sessionStorage.removeItem('oauth_gitlab_pat')

  return {
    mcpToken: tokenData.access_token,
    gitlabPat,
    projectUrl,
    targetBranch,
  }
}

export function hasPendingCallback(): boolean {
  return window.location.pathname === '/oauth/callback' && !!new URLSearchParams(window.location.search).get('code')
}

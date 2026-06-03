import { useState } from 'react'
import type { DoneEvent } from '../types'

interface ResultsProps {
  results: DoneEvent['results']
  onReset: () => void
}

type Tab = 'scan' | 'detection' | 'recommendation' | 'generation'

// Safe accessors for LLM-generated data
function str(val: unknown): string {
  if (val == null) return ''
  if (typeof val === 'string') return val
  if (typeof val === 'number' || typeof val === 'boolean') return String(val)
  return JSON.stringify(val)
}

function arr(val: unknown): Record<string, unknown>[] {
  if (Array.isArray(val)) return val as Record<string, unknown>[]
  return []
}

function Badge({ label, color }: { label: string; color: 'red' | 'yellow' | 'green' | 'blue' | 'gray' }) {
  const colors = {
    red: 'bg-red-900/60 text-red-300',
    yellow: 'bg-yellow-900/60 text-yellow-300',
    green: 'bg-green-900/60 text-green-300',
    blue: 'bg-blue-900/60 text-blue-300',
    gray: 'bg-gray-800 text-gray-400',
  }
  return <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${colors[color]}`}>{label}</span>
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">{title}</h3>
      {children}
    </div>
  )
}

function NoData() {
  return <p className="text-sm text-gray-500 italic">No data available</p>
}

function riskColor(level: string): 'red' | 'yellow' | 'green' | 'gray' {
  const l = str(level).toLowerCase()
  if (l.includes('high')) return 'red'
  if (l.includes('medium')) return 'yellow'
  if (l.includes('low')) return 'green'
  return 'gray'
}

function ScanTab({ data }: { data: Record<string, unknown> | undefined }) {
  if (!data) return <NoData />
  const services = arr(data.services)
  const databases = arr(data.databases)
  const queues = arr(data.queues)
  const caches = arr(data.caches)
  const envVars = arr(data.env_vars)
  const externalApis = arr(data.external_apis)
  const langStack = Array.isArray(data.language_stack) ? data.language_stack as string[] : []

  return (
    <div className="space-y-6">
      {langStack.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {langStack.map((l, i) => <Badge key={i} label={str(l)} color="blue" />)}
        </div>
      )}

      <Section title="Services">
        {services.length === 0 ? <NoData /> : (
          <table className="w-full text-sm">
            <thead><tr className="border-b border-gray-800 text-left text-gray-400">
              <th className="pb-2 pr-4">Name</th><th className="pb-2 pr-4">Language</th><th className="pb-2 pr-4">Framework</th><th className="pb-2">Ports</th>
            </tr></thead>
            <tbody>{services.map((s, i) => (
              <tr key={i} className="border-b border-gray-800/50">
                <td className="py-2 pr-4 font-medium text-gray-200">{str(s.name)}</td>
                <td className="py-2 pr-4 text-gray-400">{str(s.language)}</td>
                <td className="py-2 pr-4 text-gray-400">{str(s.framework)}</td>
                <td className="py-2 text-gray-400">{Array.isArray(s.ports) ? s.ports.join(', ') : str(s.ports)}</td>
              </tr>
            ))}</tbody>
          </table>
        )}
      </Section>

      {(databases.length > 0 || queues.length > 0 || caches.length > 0) && (
        <Section title="Infrastructure">
          <div className="flex flex-wrap gap-2">
            {databases.map((d, i) => <Badge key={`db-${i}`} label={`${str(d.type)}${d.version ? ` ${str(d.version)}` : ''}`} color="blue" />)}
            {queues.map((q, i) => <Badge key={`q-${i}`} label={str(q.type)} color="yellow" />)}
            {caches.map((c, i) => <Badge key={`c-${i}`} label={str(c.type)} color="green" />)}
          </div>
        </Section>
      )}

      <Section title="Environment Variables">
        {envVars.length === 0 ? <NoData /> : (
          <table className="w-full text-sm">
            <thead><tr className="border-b border-gray-800 text-left text-gray-400">
              <th className="pb-2 pr-4">Name</th><th className="pb-2 pr-4">Secret</th><th className="pb-2">Description</th>
            </tr></thead>
            <tbody>{envVars.map((v, i) => (
              <tr key={i} className="border-b border-gray-800/50">
                <td className="py-1.5 pr-4 font-mono text-xs text-gray-200">{str(v.name)}</td>
                <td className="py-1.5 pr-4">{v.is_secret ? <Badge label="SECRET" color="red" /> : <span className="text-gray-600 text-xs">—</span>}</td>
                <td className="py-1.5 text-gray-400 text-xs">{str(v.description)}</td>
              </tr>
            ))}</tbody>
          </table>
        )}
      </Section>

      {externalApis.length > 0 && (
        <Section title="External APIs">
          <div className="space-y-1">
            {externalApis.map((a, i) => (
              <div key={i} className="text-sm"><span className="text-gray-200 font-medium">{str(a.name)}</span> <span className="text-gray-500">— {str(a.purpose)}</span></div>
            ))}
          </div>
        </Section>
      )}

      <Section title="Existing Configs">
        <div className="grid grid-cols-2 gap-1 text-sm">
          {(['existing_docker_compose', 'existing_ci_cd', 'existing_iac', 'existing_local_dev'] as const).map(key => (
            <div key={key} className="flex items-center gap-2">
              <span className={data[key] ? 'text-green-400' : 'text-gray-600'}>{data[key] ? '✓' : '✗'}</span>
              <span className="text-gray-400">{key.replace('existing_', '').replace(/_/g, ' ')}</span>
            </div>
          ))}
        </div>
      </Section>
    </div>
  )
}

function DetectionTab({ data }: { data: Record<string, unknown> | undefined }) {
  if (!data) return <NoData />
  const piiFields = arr(data.pii_fields)
  const sideEffects = arr(data.side_effect_services)
  const complianceFlags = arr(data.compliance_flags)
  const riskSummary = str(data.risk_summary)

  return (
    <div className="space-y-6">
      {riskSummary && (
        <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-4 text-sm text-gray-300">{riskSummary}</div>
      )}

      <Section title="PII Fields">
        {piiFields.length === 0 ? <p className="text-sm text-green-400">No PII detected</p> : (
          <table className="w-full text-sm">
            <thead><tr className="border-b border-gray-800 text-left text-gray-400">
              <th className="pb-2 pr-4">Field</th><th className="pb-2 pr-4">Risk</th><th className="pb-2 pr-4">Source</th><th className="pb-2">Description</th>
            </tr></thead>
            <tbody>{piiFields.map((f, i) => (
              <tr key={i} className="border-b border-gray-800/50">
                <td className="py-1.5 pr-4 font-mono text-xs text-gray-200">{str(f.field_name || f.name || f.field)}</td>
                <td className="py-1.5 pr-4"><Badge label={str(f.risk_level || f.risk || 'unknown')} color={riskColor(str(f.risk_level || f.risk))} /></td>
                <td className="py-1.5 pr-4 text-gray-400 text-xs">{str(f.source_file || f.source || '')}</td>
                <td className="py-1.5 text-gray-400 text-xs">{str(f.description || '')}</td>
              </tr>
            ))}</tbody>
          </table>
        )}
      </Section>

      <Section title="Side-Effect Services">
        {sideEffects.length === 0 ? <p className="text-sm text-green-400">No side-effect services detected</p> : (
          <table className="w-full text-sm">
            <thead><tr className="border-b border-gray-800 text-left text-gray-400">
              <th className="pb-2 pr-4">Service</th><th className="pb-2 pr-4">Category</th><th className="pb-2 pr-4">Recommendation</th><th className="pb-2">Mockable</th>
            </tr></thead>
            <tbody>{sideEffects.map((s, i) => (
              <tr key={i} className="border-b border-gray-800/50">
                <td className="py-1.5 pr-4 text-gray-200">{str(s.service_name || s.name || s.service)}</td>
                <td className="py-1.5 pr-4 text-gray-400">{str(s.category || '')}</td>
                <td className="py-1.5 pr-4 text-gray-400 text-xs">{str(s.recommendation || '')}</td>
                <td className="py-1.5">{s.is_mockable ? <Badge label="Yes" color="green" /> : <Badge label="No" color="gray" />}</td>
              </tr>
            ))}</tbody>
          </table>
        )}
      </Section>

      {complianceFlags.length > 0 && (
        <Section title="Compliance Flags">
          <div className="space-y-2">
            {complianceFlags.map((f, i) => (
              <div key={i} className="rounded-lg border border-yellow-800/50 bg-yellow-950/20 px-4 py-2 text-sm text-yellow-300">
                {str(f.flag || f.name || f.type || f)} {f.description ? `— ${str(f.description)}` : ''}
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  )
}

function StrategyTab({ data }: { data: Record<string, unknown> | undefined }) {
  if (!data) return <NoData />
  const local = arr(data.local_services)
  const managed = arr(data.managed_services)
  const mocked = arr(data.mocked_services)
  const disabled = arr(data.disabled_services)
  const seedStrategy = str(data.seed_strategy)
  const filesToGenerate = arr(data.files_to_generate)

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm">
        <span className="text-gray-400">Target:</span>
        <Badge label={str(data.environment_target || 'local')} color="blue" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-lg border border-green-800/30 bg-green-950/10 p-4 space-y-2">
          <h4 className="text-sm font-semibold text-green-400">Run Locally</h4>
          {local.length === 0 ? <p className="text-xs text-gray-500">None</p> : local.map((s, i) => (
            <div key={i} className="text-sm">
              <span className="text-gray-200">{str(s.name)}</span>
              {s.image && <span className="text-gray-500 text-xs ml-1">({str(s.image)})</span>}
              {s.rationale && <p className="text-xs text-gray-500 mt-0.5">{str(s.rationale)}</p>}
            </div>
          ))}
        </div>

        <div className="rounded-lg border border-blue-800/30 bg-blue-950/10 p-4 space-y-2">
          <h4 className="text-sm font-semibold text-blue-400">Managed Services</h4>
          {managed.length === 0 ? <p className="text-xs text-gray-500">None</p> : managed.map((s, i) => (
            <div key={i} className="text-sm">
              <span className="text-gray-200">{str(s.name)}</span>
              {s.rationale && <p className="text-xs text-gray-500 mt-0.5">{str(s.rationale)}</p>}
            </div>
          ))}
        </div>

        <div className="rounded-lg border border-yellow-800/30 bg-yellow-950/10 p-4 space-y-2">
          <h4 className="text-sm font-semibold text-yellow-400">Mock / Stub</h4>
          {mocked.length === 0 ? <p className="text-xs text-gray-500">None</p> : mocked.map((s, i) => (
            <div key={i} className="text-sm">
              <span className="text-gray-200">{str(s.name || s.service_name || s)}</span>
              {s.replacement && <span className="text-gray-500 text-xs ml-1">→ {str(s.replacement)}</span>}
            </div>
          ))}
        </div>
      </div>

      {disabled.length > 0 && (
        <Section title="Disabled">
          <div className="flex flex-wrap gap-2">
            {disabled.map((s, i) => <Badge key={i} label={str(s.name || s)} color="gray" />)}
          </div>
        </Section>
      )}

      {seedStrategy && (
        <div className="rounded-lg border border-blue-800/30 bg-blue-950/10 p-3">
          <span className="text-xs text-gray-400">Seed strategy: </span>
          <span className="text-sm text-blue-300 font-medium">{seedStrategy}</span>
        </div>
      )}

      {filesToGenerate.length > 0 && (
        <Section title="Files to Generate">
          <div className="space-y-1">
            {filesToGenerate.map((f, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="text-green-400">+</span>
                <span className="font-mono text-xs text-gray-200">{str(f.path || f.file_path || f.name || f)}</span>
                {f.description && <span className="text-gray-500 text-xs">— {str(f.description)}</span>}
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  )
}

function GenerationTab({ data }: { data: Record<string, unknown> | undefined }) {
  if (!data) return <NoData />
  const files = arr(data.files_generated)
  const summary = str(data.summary)
  const branchName = str(data.branch_name)

  return (
    <div className="space-y-4">
      {(branchName || summary) && (
        <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-4 space-y-1">
          {branchName && <p className="text-sm text-gray-400">Branch: <span className="font-mono text-gray-200">{branchName}</span></p>}
          {summary && <p className="text-sm text-gray-300">{summary}</p>}
        </div>
      )}

      {files.length === 0 ? (
        <div className="text-sm text-gray-400">
          <p>No files were generated. Check the activity log for errors.</p>
          {data && <pre className="mt-4 overflow-auto rounded-lg bg-gray-900 border border-gray-800 p-4 text-xs text-gray-400">{JSON.stringify(data, null, 2)}</pre>}
        </div>
      ) : (
        files.map((file, i) => (
          <div key={i} className="rounded-lg border border-gray-800 overflow-hidden">
            <div className="bg-gray-900 px-4 py-2 border-b border-gray-800">
              <span className="text-sm font-mono text-gray-300">{str(file.file_path || file.path || `file-${i}`)}</span>
            </div>
            <pre className="overflow-auto bg-gray-950 p-4 text-sm text-gray-300 max-h-96">
              <code>{str(file.content)}</code>
            </pre>
          </div>
        ))
      )}
    </div>
  )
}

export default function Results({ results, onReset }: ResultsProps) {
  const [tab, setTab] = useState<Tab>('scan')

  const tabs: { key: Tab; label: string }[] = [
    { key: 'scan', label: 'Scan Summary' },
    { key: 'detection', label: 'Detection Report' },
    { key: 'recommendation', label: 'Strategy' },
    { key: 'generation', label: 'Generated Files' },
  ]

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

      <div>
        {tab === 'scan' && <ScanTab data={results.scan_result} />}
        {tab === 'detection' && <DetectionTab data={results.detection_result} />}
        {tab === 'recommendation' && <StrategyTab data={results.recommendation_result} />}
        {tab === 'generation' && <GenerationTab data={results.generation_result} />}
      </div>
    </div>
  )
}

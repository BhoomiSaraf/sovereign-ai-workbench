import { useEffect, useState } from 'react'
import { getRecentAudit, listTasks } from '../api/client'
import type { AuditEvent } from '../api/types'
import { useHealth } from '../hooks/useHealth'
import { Badge, EmptyState, ErrorBanner, MetricTile, Panel, Spinner } from '../components/ui'
import './SecurityPage.css'

interface ToolTally {
  [tool: string]: number
}

export default function SecurityPage() {
  const { health, error: healthError, loading } = useHealth(3000)
  const [modelCalls, setModelCalls] = useState(0)
  const [visionCalls, setVisionCalls] = useState(0)
  const [toolTally, setToolTally] = useState<ToolTally>({})
  const [taskError, setTaskError] = useState<string | null>(null)

  const [auditEvents, setAuditEvents] = useState<AuditEvent[] | null>(null)
  const [auditError, setAuditError] = useState<string | null>(null)

  // Poll append-only audit log every 3 seconds
  useEffect(() => {
    function poll() {
      getRecentAudit(60)
        .then((res) => {
          setAuditEvents(res.events)
          setAuditError(null)
        })
        .catch((err) => setAuditError(err instanceof Error ? err.message : 'Failed to poll audit log'))
    }

    poll()
    const id = window.setInterval(poll, 3000)
    return () => window.clearInterval(id)
  }, [])

  // Aggregate local tool invocations from task history
  useEffect(() => {
    listTasks()
      .then((res) => {
        let generation = 0
        let vision = 0
        const tally: ToolTally = {}

        for (const task of res.tasks) {
          for (const event of task.events ?? []) {
            if (event.type === 'generation') generation += 1
            if (event.type === 'vision_analysis') vision += 1
            if (event.type === 'tool' && event.status === 'complete') {
              const tool = String(event.tool ?? 'unknown')
              tally[tool] = (tally[tool] ?? 0) + 1
            }
          }
        }

        setModelCalls(generation)
        setVisionCalls(vision)
        setToolTally(tally)
      })
      .catch((err) => setTaskError(err instanceof Error ? err.message : 'Failed to load task telemetry'))
  }, [])

  const network = health?.network
  const externalCalls = network?.external_connections_detected ?? 0

  return (
    <div className="security-page">
      <div className="security-header">
        <div>
          <h1>Sovereignty &amp; Air-Gap Verification Monitor</h1>
          <p className="security-desc">
            Technical proof of zero external data leakage. All AI inference, embeddings, OCR, tool execution, and artifact compilation run exclusively on-premises.
          </p>
        </div>
        <Badge tone={externalCalls === 0 ? 'ok' : 'err'} size="md" glow>
          {externalCalls === 0 ? 'ZERO EXTERNAL EGRESS' : 'EGRESS DETECTED'}
        </Badge>
      </div>

      {healthError && <ErrorBanner title="Monitor Notice" message={healthError} />}

      {/* Sovereignty Verification Metrics */}
      <div className="security-metrics-grid">
        <MetricTile
          label="Sovereignty Mode"
          value={network?.sovereign_mode ? 'AIR-GAPPED' : 'PERMITTED'}
          detail="Network Policy: Strict Non-Local Host Blocking"
          status={network?.sovereign_mode ? 'ok' : 'warn'}
        />
        <MetricTile
          label="External Network Calls"
          value={externalCalls}
          detail="Outbound Cloud API Calls Blocked"
          status={externalCalls === 0 ? 'ok' : 'err'}
        />
        <MetricTile
          label="Local LLM Inference Calls"
          value={modelCalls}
          detail="Direct to On-Premise Ollama Engine"
          status="info"
        />
        <MetricTile
          label="On-Device Vision / OCR Runs"
          value={visionCalls}
          detail="Processed via Local Qwen-VL & PyMuPDF"
          status="info"
        />
      </div>

      {/* Local Tool Execution Audit */}
      <Panel title="On-Premise Tool Invocations Breakdown">
        {taskError && <ErrorBanner message={taskError} />}
        {Object.keys(toolTally).length === 0 ? (
          <EmptyState message="No local tools invoked yet this session. Run an agentic task to see tool telemetry." />
        ) : (
          <div className="tool-stats-grid">
            {Object.entries(toolTally).map(([tool, count]) => (
              <div key={tool} className="tool-stat-card">
                <span className="tool-stat-name">{tool}</span>
                <span className="tool-stat-count">{count} Invocations</span>
              </div>
            ))}
          </div>
        )}
      </Panel>

      {/* Live Append-Only Audit Stream */}
      <Panel
        title="Live Append-Only Audit Trail"
        action={<Badge tone="accent" size="sm">LIVE · logs/audit.jsonl</Badge>}
      >
        {auditError && <ErrorBanner message={auditError} />}
        {loading && !auditEvents && (
          <div className="audit-loading">
            <Spinner size="md" /> Reading local audit stream…
          </div>
        )}

        {auditEvents && auditEvents.length === 0 && (
          <EmptyState message="No audit records captured yet. Actions like task starts, tool calls, and completions are recorded here." />
        )}

        {auditEvents && auditEvents.length > 0 && (
          <div className="audit-table-wrapper">
            <table className="audit-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Event Type</th>
                  <th>Task ID</th>
                  <th>Status</th>
                  <th>Audit Payload</th>
                </tr>
              </thead>
              <tbody>
                {auditEvents
                  .slice()
                  .reverse()
                  .map((ev, i) => {
                    const details = ev.details ? JSON.stringify(ev.details) : '—'

                    return (
                      <tr key={i}>
                        <td className="audit-time-cell">
                          {new Date(ev.timestamp).toLocaleTimeString()}
                        </td>
                        <td>
                          <span className="audit-type-tag">{ev.event_type}</span>
                        </td>
                        <td>
                          <code className="audit-task-code">
                            {ev.task_id ? ev.task_id.slice(0, 8) : 'SYSTEM'}
                          </code>
                        </td>
                        <td>
                          <Badge tone={ev.status === 'error' ? 'err' : 'ok'} size="sm">
                            {ev.status}
                          </Badge>
                        </td>
                        <td className="audit-payload-cell">
                          <code>{details}</code>
                        </td>
                      </tr>
                    )
                  })}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { getRecentAudit, listTasks } from '../api/client'
import type { AuditEvent } from '../api/types'
import { useHealth } from '../hooks/useHealth'
import { Badge, EmptyState, ErrorBanner, Panel } from '../components/ui'
import './SecurityPage.css'

interface ToolTally {
  [tool: string]: number
}

export default function SecurityPage() {
  const { health, error: healthError, loading } = useHealth(4000)
  const [modelCalls, setModelCalls] = useState(0)
  const [visionCalls, setVisionCalls] = useState(0)
  const [toolTally, setToolTally] = useState<ToolTally>({})
  const [taskError, setTaskError] = useState<string | null>(null)

  const [auditEvents, setAuditEvents] = useState<AuditEvent[] | null>(null)
  const [auditError, setAuditError] = useState<string | null>(null)

  useEffect(() => {
    function poll() {
      getRecentAudit(50)
        .then((res) => {
          setAuditEvents(res.events)
          setAuditError(null)
        })
        .catch((err) => setAuditError(err instanceof Error ? err.message : 'Failed to load audit log'))
    }

    poll()
    const id = window.setInterval(poll, 5000)
    return () => window.clearInterval(id)
  }, [])

  // Real counters derived from every task's actual execution trace
  // (GET /tasks -> events[]) rather than invented demo numbers.
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
      .catch((err) => setTaskError(err instanceof Error ? err.message : 'Failed to load task history'))
  }, [])

  const network = health?.network

  return (
    <div>
      <h1>Security Monitor</h1>

      <Panel title="Sovereignty status">
        {healthError && <ErrorBanner message={healthError} />}
        {loading && !health && <EmptyState message="Checking…" />}
        {network && (
          <div className="sov-grid">
            <div className={`sov-stat ${network.sovereign_mode ? 'sov-ok' : 'sov-warn'}`}>
              <div className="sov-stat-label">Sovereign mode</div>
              <div className="sov-stat-value">{network.sovereign_mode ? 'AIR-GAPPED / LOCAL' : 'PERMITTED'}</div>
            </div>
            <div className={`sov-stat ${network.external_connections_detected === 0 ? 'sov-ok' : 'sov-err'}`}>
              <div className="sov-stat-label">External calls detected</div>
              <div className="sov-stat-value">{network.external_connections_detected}</div>
            </div>
            <div className="sov-stat">
              <div className="sov-stat-label">External network allowed</div>
              <div className="sov-stat-value">{network.external_network_allowed ? 'Yes' : 'No'}</div>
            </div>
          </div>
        )}
        {network && <p className="sov-message">{network.message}</p>}
        <p className="sov-caveat">
          This reflects the application-level <code>NetworkMonitor</code> only — it complements, and does
          not replace, OS/firewall-level network isolation.
        </p>
      </Panel>

      <Panel title="Local activity (from executed tasks)">
        {taskError && <ErrorBanner message={taskError} />}
        <div className="activity-grid">
          <ActivityStat label="Model generation calls" value={modelCalls} />
          <ActivityStat label="Vision analysis calls" value={visionCalls} />
          {Object.entries(toolTally).map(([tool, count]) => (
            <ActivityStat key={tool} label={`Tool: ${tool}`} value={count} />
          ))}
        </div>
      </Panel>

      <Panel title="Audit trail" action={<Badge tone="accent">live · logs/audit.jsonl</Badge>}>
        {auditError && <ErrorBanner message={auditError} />}
        {auditEvents && auditEvents.length === 0 && (
          <EmptyState message="No audit events recorded yet. Run a task to populate the log." />
        )}
        {auditEvents && auditEvents.length > 0 && (
          <ul className="audit-log">
            {auditEvents
              .slice()
              .reverse()
              .map((event, i) => (
                <li key={i} className="audit-log-row">
                  <span className="audit-time">{new Date(event.timestamp).toLocaleTimeString()}</span>
                  <Badge tone={event.status === 'error' ? 'err' : 'ok'}>{event.event_type}</Badge>
                  {event.task_id && <span className="audit-task">{event.task_id.slice(0, 8)}</span>}
                </li>
              ))}
          </ul>
        )}
      </Panel>
    </div>
  )
}

function ActivityStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="activity-stat">
      <div className="activity-stat-value">{value}</div>
      <div className="activity-stat-label">{label}</div>
    </div>
  )
}

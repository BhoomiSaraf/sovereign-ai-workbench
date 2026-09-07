import type { AgentEvent } from '../api/types'
import { EmptyState } from './ui'
import './ExecutionTrace.css'

// Friendly labels for event types the backend is known to emit today
// (see AgentState.add_event calls in app/agent/executor.py). This is a
// display-only lookup — any event type not listed here still renders
// correctly using its raw type/tool fields, so new event types added on
// the backend show up without a frontend change.
const TYPE_LABELS: Record<string, string> = {
  routing: 'Model routing',
  tool_selection: 'Tool selection',
  tool: 'Tool execution',
  vision_analysis: 'Vision analysis',
  artifact_generation: 'Artifact generation',
  generation: 'Response generation',
  execution: 'Execution',
}

const STATUS_ICON: Record<string, string> = {
  complete: '✓',
  success: '✓',
  error: '✕',
  failed: '✕',
  skipped: '–',
  running: '…',
  pending: '…',
}

function describeEvent(event: AgentEvent): string {
  const base = TYPE_LABELS[event.type] ?? event.type
  const tool = typeof event.tool === 'object' ? undefined : event.tool
  return tool ? `${base}: ${tool}` : base
}

function statusTone(status: string): string {
  if (status === 'error' || status === 'failed') return 'err'
  if (status === 'skipped') return 'skip'
  if (status === 'running' || status === 'pending') return 'pending'
  return 'ok'
}

export default function ExecutionTrace({ events }: { events: AgentEvent[] }) {
  if (!events || events.length === 0) {
    return <EmptyState message="No execution trace yet. Run a task to see live steps here." />
  }

  return (
    <ol className="trace">
      {events.map((event, i) => {
        const tone = statusTone(event.status)
        const icon = STATUS_ICON[event.status] ?? '•'
        const detailKeys = Object.keys(event).filter((k) => k !== 'type' && k !== 'status')

        return (
          <li key={i} className={`trace-step trace-${tone}`}>
            <span className={`trace-icon trace-icon-${tone}`}>{icon}</span>
            <div className="trace-body">
              <div className="trace-label">{describeEvent(event)}</div>
              {detailKeys.length > 0 && (
                <div className="trace-details">
                  {detailKeys.map((key) => {
                    const value = event[key]
                    if (value === null || value === undefined || value === '') return null
                    const rendered = typeof value === 'object' ? JSON.stringify(value) : String(value)
                    return (
                      <span key={key} className="trace-detail">
                        <span className="trace-detail-key">{key}:</span> {rendered}
                      </span>
                    )
                  })}
                </div>
              )}
            </div>
          </li>
        )
      })}
    </ol>
  )
}

import { useState } from 'react'
import type { AgentEvent } from '../api/types'
import { Badge, EmptyState } from './ui'
import './ExecutionTrace.css'

const PIPELINE_STAGES = [
  { id: 'plan', label: 'PLAN' },
  { id: 'routing', label: 'ROUTE MODEL' },
  { id: 'tools', label: 'SELECT TOOLS' },
  { id: 'document', label: 'READ FILE' },
  { id: 'knowledge', label: 'SEARCH RAG' },
  { id: 'analysis', label: 'ANALYZE' },
  { id: 'generation', label: 'GENERATE' },
  { id: 'validation', label: 'VALIDATE' },
]

const TYPE_LABELS: Record<string, string> = {
  routing: 'Model Auto-Selection',
  tool_selection: 'Tool Selection & Security Policy',
  tool: 'Local Sandboxed Tool Execution',
  vision_analysis: 'Multimodal Vision & OCR Reasoning',
  document_analysis: 'Document Parsing & Extraction',
  knowledge_search: 'Local RAG Vector Search',
  artifact_generation: 'Deliverable File Generation',
  generation: 'On-Premise LLM Inference',
  execution: 'Task Lifecycle Event',
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

function statusTone(status: string): 'ok' | 'err' | 'warn' | 'neutral' {
  if (status === 'error' || status === 'failed') return 'err'
  if (status === 'skipped') return 'warn'
  if (status === 'running' || status === 'pending') return 'warn'
  return 'ok'
}

export default function ExecutionTrace({ events }: { events: AgentEvent[] }) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null)
  const [showRaw, setShowRaw] = useState(false)

  if (!events || events.length === 0) {
    return <EmptyState message="No execution trace recorded. Run a task to see live step-by-step agent actions." />
  }

  // Detect which high-level pipeline stages were engaged
  const activeStages = new Set<string>()
  for (const ev of events) {
    if (ev.type === 'routing') activeStages.add('routing')
    if (ev.type === 'tool_selection') activeStages.add('tools')
    if (ev.type === 'document_analysis' || ev.tool === 'documents' || ev.tool === 'pdf') activeStages.add('document')
    if (ev.type === 'knowledge_search' || ev.tool === 'knowledge_search') activeStages.add('knowledge')
    if (ev.type === 'vision_analysis' || ev.tool === 'vision') activeStages.add('analysis')
    if (ev.type === 'generation') activeStages.add('generation')
    if (ev.type === 'artifact_generation' || ev.tool === 'artifact') activeStages.add('validation')
    if (ev.terminal_tool) activeStages.add('validation')
  }
  activeStages.add('plan')

  return (
    <div className="trace-container">
      {/* High-level Agentic Pipeline Flowchart */}
      <div className="pipeline-flowchart">
        <div className="flowchart-title">Agentic Execution Pipeline</div>
        <div className="flowchart-track">
          {PIPELINE_STAGES.map((stage, i) => {
            const isActive = activeStages.has(stage.id)
            return (
              <div key={stage.id} className="flowchart-node-wrapper">
                <div className={`flowchart-node ${isActive ? 'node-active' : 'node-idle'}`}>
                  <span className="node-label">{stage.label}</span>
                  {isActive && <span className="node-badge">✓</span>}
                </div>
                {i < PIPELINE_STAGES.length - 1 && (
                  <div className={`flowchart-arrow ${isActive ? 'arrow-active' : 'arrow-idle'}`}>
                    →
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Header with Toggle */}
      <div className="trace-header-row">
        <span className="trace-count">{events.length} Orchestration Steps Executed</span>
        <button className="raw-toggle-btn" onClick={() => setShowRaw(!showRaw)}>
          {showRaw ? 'Step View' : 'JSON Audit Trace'}
        </button>
      </div>

      {showRaw ? (
        <pre className="raw-trace-box">{JSON.stringify(events, null, 2)}</pre>
      ) : (
        <ol className="trace-list">
          {events.map((event, i) => {
            const tone = statusTone(event.status)
            const icon = STATUS_ICON[event.status] ?? '•'
            const isExpanded = expandedIndex === i
            const label = TYPE_LABELS[event.type] ?? event.type
            const toolName = typeof event.tool === 'string' ? event.tool : undefined
            const detailKeys = Object.keys(event).filter((k) => k !== 'type' && k !== 'status' && k !== 'tool')

            return (
              <li key={i} className={`trace-card trace-card-${tone}`}>
                <div
                  className="trace-card-header"
                  onClick={() => setExpandedIndex(isExpanded ? null : i)}
                >
                  <div className="trace-card-left">
                    <span className={`trace-bullet trace-bullet-${tone}`}>{icon}</span>
                    <span className="trace-card-title">{label}</span>
                    {toolName && <Badge tone="accent" size="sm">Tool: {toolName}</Badge>}
                  </div>

                  <div className="trace-card-right">
                    <Badge tone={tone} size="sm">{event.status}</Badge>
                    <span className="trace-expand-icon">{isExpanded ? '▲' : '▼'}</span>
                  </div>
                </div>

                {detailKeys.length > 0 && (
                  <div className={`trace-card-body ${isExpanded ? 'body-expanded' : 'body-collapsed'}`}>
                    <div className="trace-details-grid">
                      {detailKeys.map((key) => {
                        const val = event[key]
                        if (val === null || val === undefined || val === '') return null
                        const formatted = typeof val === 'object' ? JSON.stringify(val, null, 1) : String(val)

                        return (
                          <div key={key} className="trace-detail-item">
                            <span className="detail-key">{key}:</span>
                            <span className="detail-val">{formatted}</span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}
              </li>
            )
          })}
        </ol>
      )}
    </div>
  )
}

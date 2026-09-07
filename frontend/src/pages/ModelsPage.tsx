import { useEffect, useState } from 'react'
import { listModels, routeModel } from '../api/client'
import type { ModelsResponse, RouteDecision } from '../api/types'
import { Badge, EmptyState, ErrorBanner, Panel, Spinner } from '../components/ui'
import './ModelsPage.css'

function getDynamicModelMeta(m: { name: string; capabilities: Record<string, number>; modalities: string[] }): {
  role: string
  desc: string
} {
  const caps = Object.entries(m.capabilities).sort((a, b) => b[1] - a[1])
  const topCap = caps[0]?.[0] || 'general'
  const secondCap = caps[1]?.[0] || ''

  if (m.modalities.includes('image') || topCap === 'vision' || topCap === 'document_vision') {
    return {
      role: 'Multimodal Vision & Diagram OCR',
      desc: `Specialized in image reasoning, P&ID schematics, engineering drawings, and visual inspection.`,
    }
  }

  if (topCap === 'coding' || topCap === 'programming' || topCap === 'debugging') {
    return {
      role: 'Python Coding & Sandboxed Math Engine',
      desc: `Fine-tuned for code generation, bug fixing, script execution, and calculation formulas.`,
    }
  }

  return {
    role: `${topCap.charAt(0).toUpperCase() + topCap.slice(1).replace('_', ' ')} & Reasoning Engine`,
    desc: `Optimized for multi-step agent planning, report summarization, and organizational knowledge reasoning${secondCap ? ` (${secondCap.replace('_', ' ')})` : ''}.`,
  }
}

const ROUTING_PRESETS = [
  { label: 'Debug Python Memory Leak', task: 'Debug this Python script that reads SCADA CSV data and fix the memory leak', hasImage: false },
  { label: 'Summarize Inspection Report', task: 'Summarize this scanned heat exchanger inspection report and draft an approval note', hasImage: false },
  { label: 'Analyze P&ID Engineering Drawing', task: 'Analyze this scanned P&ID drawing and identify all pressure safety valve bypass tags', hasImage: true },
  { label: 'Check SOP Maintenance Policy', task: 'According to our internal pump maintenance SOP, what is the maximum permissible vibration amplitude?', hasImage: false },
]

export default function ModelsPage() {
  const [models, setModels] = useState<ModelsResponse | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  const [task, setTask] = useState('')
  const [hasImage, setHasImage] = useState(false)
  const [routing, setRouting] = useState(false)
  const [decision, setDecision] = useState<RouteDecision | null>(null)
  const [routeError, setRouteError] = useState<string | null>(null)

  useEffect(() => {
    listModels()
      .then(setModels)
      .catch((err) => setLoadError(err instanceof Error ? err.message : 'Failed to load registered models'))
  }, [])

  async function handleTest(e?: React.FormEvent) {
    if (e) e.preventDefault()
    if (!task.trim()) return

    setRouting(true)
    setRouteError(null)
    setDecision(null)

    try {
      const res = await routeModel(task, hasImage)
      setDecision(res)
    } catch (err) {
      setRouteError(err instanceof Error ? err.message : 'Routing preview failed')
    } finally {
      setRouting(false)
    }
  }

  function applyPreset(presetTask: string, presetHasImage: boolean) {
    setTask(presetTask)
    setHasImage(presetHasImage)
    routeModel(presetTask, presetHasImage)
      .then(setDecision)
      .catch((err) => setRouteError(err instanceof Error ? err.message : 'Routing failed'))
  }

  return (
    <div className="models-container">
      <div className="models-header-row">
        <div>
          <h1>Model Registry &amp; Intelligent Routing</h1>
          <p className="models-desc">
            The Sovereign AI Workbench is strictly model-agnostic. Multiple open-weight local models operate concurrently on-premise, and tasks are automatically directed to the optimal model based on capability requirements.
          </p>
        </div>
        <div className="hardware-spec-pill">
          <span className="pill-title">Hardware Architecture:</span>
          <strong>Local GPU (8GB VRAM Target)</strong>
        </div>
      </div>

      {loadError && <ErrorBanner title="Model Catalog Notice" message={loadError} />}

      {/* Model Catalog Grid */}
      <Panel title={`Registered On-Premise Models (${models ? models.count : '...'})`}>
        {!models && !loadError && (
          <div className="models-loading">
            <Spinner size="md" /> Loading registered models catalog…
          </div>
        )}

        {models && models.count === 0 && <EmptyState message="No models currently registered." />}

        {models && models.count > 0 && (
          <div className="models-grid">
            {models.models.map((m) => {
              const meta = getDynamicModelMeta(m)

              return (
                <div key={m.name} className="model-box">
                  <div className="model-box-header">
                    <div className="model-title-group">
                      <div>
                        <h4 className="model-name">{m.name}</h4>
                        <span className="model-ollama-tag">{m.ollama_name}</span>
                      </div>
                    </div>
                    <div className="model-tags">
                      {m.modalities.map((mod) => (
                        <Badge key={mod} tone={mod === 'image' ? 'accent' : 'neutral'} size="sm">
                          {mod.toUpperCase()}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div className="model-role-badge">
                    <strong>Role:</strong> {meta.role}
                  </div>
                  <p className="model-role-desc">{meta.desc}</p>

                  <div className="capabilities-section">
                    <span className="caps-title">Capability Ratings (0–5):</span>
                    <div className="caps-list">
                      {Object.entries(m.capabilities)
                        .sort((a, b) => b[1] - a[1])
                        .map(([cap, strength]) => (
                          <div key={cap} className="cap-item">
                            <span className="cap-label">{cap}</span>
                            <div className="cap-meter">
                              <div
                                className={`cap-fill ${strength >= 4 ? 'cap-fill-high' : 'cap-fill-med'}`}
                                style={{ width: `${(strength / 5) * 100}%` }}
                              />
                            </div>
                            <span className="cap-num">{strength}/5</span>
                          </div>
                        ))}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </Panel>

      {/* Interactive Model Routing Sandbox */}
      <Panel title="Interactive Model Auto-Selection Simulator">
        <div className="route-tester-intro">
          <p>
            Test any task prompt below to see how the rule-based and capability-scoring router automatically assigns the task to the right model without hard-coding.
          </p>
          <div className="preset-test-buttons">
            <span className="preset-test-label">Common Industrial Tasks:</span>
            {ROUTING_PRESETS.map((p, i) => (
              <button
                key={i}
                type="button"
                className="preset-test-btn"
                onClick={() => applyPreset(p.task, p.hasImage)}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleTest} className="route-test-form">
          <div className="route-input-group">
            <input
              type="text"
              className="route-input"
              placeholder='e.g. "Write Python code to compute refinery pipe stress" or "Review this scanned P&ID"'
              value={task}
              onChange={(e) => setTask(e.target.value)}
            />
            <label className="route-checkbox-label">
              <input
                type="checkbox"
                checked={hasImage}
                onChange={(e) => setHasImage(e.target.checked)}
              />
              <span>Has Image / Drawing</span>
            </label>
            <button
              type="submit"
              className="route-submit-btn"
              disabled={routing || !task.trim()}
            >
              {routing ? <Spinner size="sm" /> : 'Evaluate Routing'}
            </button>
          </div>
        </form>

        {routeError && <ErrorBanner title="Routing Calculation Notice" message={routeError} />}

        {decision && (
          <div className="decision-result-panel">
            <div className="decision-result-header">
              <div>
                <span className="decision-subtitle">ROUTING ENGINE DETERMINATION:</span>
                <div className="decision-chosen-model">{decision.selected_model}</div>
              </div>
              <Badge tone="accent" size="md" glow>
                Capability Score: {decision.score.toFixed(1)}
              </Badge>
            </div>

            <div className="decision-metrics-row">
              <div className="decision-metric">
                <span className="dm-label">Primary Modality:</span>
                <strong>{decision.has_image ? 'Multimodal (Text + Vision)' : 'Text Only'}</strong>
              </div>
              <div className="decision-metric">
                <span className="dm-label">Estimated Complexity:</span>
                <strong>{decision.task_requirements.complexity.toUpperCase()}</strong>
              </div>
              <div className="decision-metric">
                <span className="dm-label">RAG Required:</span>
                <strong>{decision.task_requirements.rag_required ? 'YES (Vector Search)' : 'NO'}</strong>
              </div>
            </div>

            <div className="decision-reasons-box">
              <span className="reasons-title">Explainability Audit Trail:</span>
              <ul className="reasons-list">
                {decision.reason.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </Panel>
    </div>
  )
}

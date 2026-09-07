import { useEffect, useState } from 'react'
import { listModels, routeModel } from '../api/client'
import type { ModelsResponse, RouteDecision } from '../api/types'
import { Badge, EmptyState, ErrorBanner, Panel, Spinner } from '../components/ui'
import './ModelsPage.css'

const MODALITY_TONE: Record<string, 'accent' | 'neutral'> = {
  image: 'accent',
  text: 'neutral',
}

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
      .catch((err) => setLoadError(err instanceof Error ? err.message : 'Failed to load models'))
  }, [])

  async function handleTest(e: React.FormEvent) {
    e.preventDefault()
    if (!task.trim()) return

    setRouting(true)
    setRouteError(null)
    setDecision(null)

    try {
      const res = await routeModel(task, hasImage)
      setDecision(res)
    } catch (err) {
      setRouteError(err instanceof Error ? err.message : 'Routing failed')
    } finally {
      setRouting(false)
    }
  }

  return (
    <div>
      <h1>Models</h1>

      {loadError && <ErrorBanner message={loadError} />}

      <Panel title={`Registered local models${models ? ` (${models.count})` : ''}`}>
        {!models && !loadError && <EmptyState message="Loading model registry…" />}
        {models && models.count === 0 && <EmptyState message="No models are registered." />}
        {models && models.count > 0 && (
          <div className="model-cards">
            {models.models.map((m) => (
              <div key={m.name} className="model-card">
                <div className="model-card-header">
                  <span className="model-card-name">{m.name}</span>
                  <span className="model-card-ollama">{m.ollama_name}</span>
                </div>
                <div className="model-card-modalities">
                  {m.modalities.map((mod) => (
                    <Badge key={mod} tone={MODALITY_TONE[mod] ?? 'neutral'}>
                      {mod}
                    </Badge>
                  ))}
                </div>
                <div className="model-card-caps">
                  {Object.entries(m.capabilities)
                    .sort((a, b) => b[1] - a[1])
                    .map(([cap, strength]) => (
                      <div key={cap} className="cap-row">
                        <span className="cap-name">{cap}</span>
                        <div className="cap-bar">
                          <div className="cap-bar-fill" style={{ width: `${(strength / 5) * 100}%` }} />
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>

      <Panel title="Test model auto-selection">
        <form onSubmit={handleTest} className="route-test-form">
          <input
            type="text"
            placeholder='e.g. "Write Python to analyze this CSV" or "Analyze this P&ID"'
            value={task}
            onChange={(e) => setTask(e.target.value)}
          />
          <label className="route-test-checkbox">
            <input type="checkbox" checked={hasImage} onChange={(e) => setHasImage(e.target.checked)} />
            has image
          </label>
          <button type="submit" disabled={routing || !task.trim()}>
            {routing ? <Spinner /> : 'Route'}
          </button>
        </form>

        {routeError && <ErrorBanner message={routeError} />}

        {decision && (
          <div className="route-result">
            <div className="route-result-model">
              Selected: <strong>{decision.selected_model}</strong>{' '}
              <span className="route-result-score">score {decision.score}</span>
            </div>
            <ul className="route-reasons">
              {decision.reason.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>
        )}
      </Panel>
    </div>
  )
}

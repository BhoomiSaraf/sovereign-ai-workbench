import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listModels, listTasks } from '../api/client'
import type { ModelsResponse, TaskListResponse } from '../api/types'
import { useHealth } from '../hooks/useHealth'
import { Badge, EmptyState, ErrorBanner, MetricTile, Panel } from '../components/ui'
import './Dashboard.css'

export default function Dashboard() {
  const { health, error: healthError } = useHealth()
  const [models, setModels] = useState<ModelsResponse | null>(null)
  const [tasks, setTasks] = useState<TaskListResponse | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([listModels(), listTasks()])
      .then(([m, t]) => {
        setModels(m)
        setTasks(t)
      })
      .catch((err) => setLoadError(err instanceof Error ? err.message : 'Failed to load system metrics'))
  }, [])

  const recentTasks = tasks?.tasks.slice(-6).reverse() ?? []
  const externalCalls = health?.network?.external_connections_detected ?? 0

  return (
    <div className="dashboard-container">
      {/* Welcome Banner */}
      <div className="welcome-banner">
        <div>
          <h1 className="welcome-title">Sovereign AI Industrial Workbench</h1>
          <p className="welcome-desc">
            Air-gapped, on-premise AI platform engineered for confidential workloads in refineries, PSUs, and defense-linked manufacturing.
          </p>
        </div>
        <Link to="/workspace" className="primary-action-btn">
          Launch Task Workspace →
        </Link>
      </div>

      {/* Metric Tiles Row */}
      <div className="dashboard-metrics-grid">
        <MetricTile
          label="Sovereignty Status"
          value={health?.network?.sovereign_mode ? 'AIR-GAPPED' : 'ONLINE'}
          detail="100% Local Inference & Storage"
          status={health?.network?.sovereign_mode ? 'ok' : 'warn'}
        />
        <MetricTile
          label="External Network Egress"
          value={`${externalCalls} Calls`}
          detail="Zero External API Contact"
          status={externalCalls === 0 ? 'ok' : 'err'}
        />
        <MetricTile
          label="Registered Local Models"
          value={models ? `${models.count} Models` : '...'}
          detail="Qwen3 4B / Coder 7B / VL 3B"
          status="info"
        />
        <MetricTile
          label="Python Code Sandbox"
          value="ISOLATED"
          detail="Network: None · Read-Only FS"
          status="ok"
        />
      </div>

      {loadError && <ErrorBanner title="Dashboard Notice" message={loadError} />}
      {healthError && <ErrorBanner title="Backend Status" message={healthError} tip="Ensure the local backend is running on http://localhost:8000." />}

      {/* Recent Tasks and System Info */}
      <div className="dashboard-split-grid">
        <Panel
          title="Recent Task Orchestrations"
          action={<Link to="/workspace" className="panel-link">New Task →</Link>}
        >
          {recentTasks.length === 0 ? (
            <EmptyState
              message="No agent tasks executed yet in this session. Launch a task from the workspace to begin."
            />
          ) : (
            <ul className="dashboard-task-list">
              {recentTasks.map((t) => (
                <li key={t.task_id} className="dashboard-task-row">
                  <div className="task-row-main">
                    <span className="task-row-id">#{t.task_id.slice(0, 8)}</span>
                    <span className="task-row-prompt">
                      {t.prompt || t.response?.slice(0, 70) || 'Task Executed'}
                    </span>
                  </div>
                  <div className="task-row-meta">
                    {t.selected_model && (
                      <span className="task-model-pill">{t.selected_model}</span>
                    )}
                    <Badge tone={t.status === 'success' ? 'ok' : t.status === 'error' ? 'err' : 'neutral'} size="sm">
                      {t.status ?? 'completed'}
                    </Badge>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel title="Sovereign Architecture Principles">
          <ul className="principles-list">
            <li>
              <strong>100% Air-Gapped:</strong> Zero telemetry or prompts leave organizational premises.
            </li>
            <li>
              <strong>Model-Agnostic:</strong> Modular registry supports adding new open-weight models seamlessly.
            </li>
            <li>
              <strong>Agentic Multi-Step:</strong> Autonomous tool calling, file I/O, OCR, and document compilation.
            </li>
            <li>
              <strong>Auditable Execution:</strong> Append-only local logging for compliance and verification.
            </li>
          </ul>
        </Panel>
      </div>
    </div>
  )
}

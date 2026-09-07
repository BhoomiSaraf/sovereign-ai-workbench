import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listModels, listTasks } from '../api/client'
import type { ModelsResponse, TaskListResponse } from '../api/types'
import { useHealth } from '../hooks/useHealth'
import { Badge, EmptyState, ErrorBanner, Panel, Spinner } from '../components/ui'
import './Dashboard.css'

export default function Dashboard() {
  const { health, error: healthError, loading: healthLoading } = useHealth()
  const [models, setModels] = useState<ModelsResponse | null>(null)
  const [tasks, setTasks] = useState<TaskListResponse | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([listModels(), listTasks()])
      .then(([m, t]) => {
        setModels(m)
        setTasks(t)
      })
      .catch((err) => setLoadError(err instanceof Error ? err.message : 'Failed to load'))
  }, [])

  const recentTasks = tasks?.tasks.slice(-5).reverse() ?? []

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>

      <div className="dashboard-tiles">
        <StatusTile
          label="Backend"
          ok={!healthError && !healthLoading}
          loading={healthLoading}
          detail={healthError ?? 'Reachable'}
        />
        <StatusTile
          label="Sovereign mode"
          ok={health?.network?.sovereign_mode ?? null}
          loading={healthLoading}
          detail={health?.network?.message ?? '—'}
        />
        <StatusTile
          label="External calls"
          ok={health ? health.network.external_connections_detected === 0 : null}
          loading={healthLoading}
          detail={health ? String(health.network.external_connections_detected) : '—'}
        />
        <StatusTile
          label="Registered models"
          ok={models ? models.count > 0 : null}
          loading={!models && !loadError}
          detail={models ? `${models.count} local` : '—'}
        />
      </div>

      {loadError && <ErrorBanner message={loadError} />}

      <div className="dashboard-grid">
        <Panel title="Recent tasks" action={<Link to="/workspace">New task →</Link>}>
          {recentTasks.length === 0 ? (
            <EmptyState message="No tasks have been run yet." />
          ) : (
            <ul className="task-list">
              {recentTasks.map((t) => (
                <li key={t.task_id} className="task-list-item">
                  <span className="task-id">{t.task_id.slice(0, 8)}</span>
                  <span className="task-prompt">{t.prompt ?? t.response?.slice(0, 60) ?? '—'}</span>
                  <Badge tone={t.status === 'success' ? 'ok' : t.status === 'error' ? 'err' : 'neutral'}>
                    {t.status ?? 'unknown'}
                  </Badge>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel title="Quick links">
          <div className="quick-links">
            <Link to="/workspace">Start a task →</Link>
            <Link to="/knowledge">Upload &amp; search knowledge base →</Link>
            <Link to="/models">View model registry &amp; routing →</Link>
            <Link to="/security">Open sovereignty monitor →</Link>
          </div>
        </Panel>
      </div>
    </div>
  )
}

function StatusTile({
  label,
  ok,
  loading,
  detail,
}: {
  label: string
  ok: boolean | null
  loading: boolean
  detail: string
}) {
  const tone = loading ? 'neutral' : ok ? 'ok' : ok === false ? 'err' : 'neutral'
  return (
    <div className={`status-tile status-tile-${tone}`}>
      <div className="status-tile-label">{label}</div>
      <div className="status-tile-value">
        {loading ? <Spinner /> : ok ? '✓' : ok === false ? '✕' : '—'}
      </div>
      <div className="status-tile-detail">{detail}</div>
    </div>
  )
}

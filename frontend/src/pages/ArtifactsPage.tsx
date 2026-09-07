import { useEffect, useState } from 'react'
import { artifactDownloadUrl, listTasks } from '../api/client'
import { Badge, EmptyState, ErrorBanner, Panel, Spinner } from '../components/ui'
import './ArtifactsPage.css'

interface ArtifactRow {
  taskId: string
  path: string
  type: string
  validation: unknown
}

export default function ArtifactsPage() {
  const [rows, setRows] = useState<ArtifactRow[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    listTasks()
      .then((res) => {
        const extracted: ArtifactRow[] = []

        for (const task of res.tasks) {
          const path = task.metadata?.artifact_path as string | undefined
          if (!path) continue

          extracted.push({
            taskId: task.task_id,
            path,
            type: (task.metadata?.artifact_type as string) ?? 'unknown',
            validation: task.metadata?.artifact_validation,
          })
        }

        setRows(extracted.reverse())
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load artifacts'))
  }, [])

  return (
    <div>
      <h1>Artifacts</h1>
      <p className="artifacts-note">
        Derived from generated artifacts recorded on completed tasks. Files are served from{' '}
        <code>data/artifacts/</code> by the backend on demand.
      </p>

      {error && <ErrorBanner message={error} />}

      <Panel title="Generated artifacts">
        {!rows && !error && (
          <div className="artifacts-loading">
            <Spinner /> Loading…
          </div>
        )}
        {rows && rows.length === 0 && (
          <EmptyState message="No artifacts have been generated yet. Run a task that produces a document to see it here." />
        )}
        {rows && rows.length > 0 && (
          <table className="artifacts-table">
            <thead>
              <tr>
                <th>Task</th>
                <th>Type</th>
                <th>Path</th>
                <th>Validation</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.taskId}>
                  <td className="mono">{row.taskId.slice(0, 8)}</td>
                  <td>
                    <Badge tone="accent">{row.type}</Badge>
                  </td>
                  <td className="mono path-cell">{row.path}</td>
                  <td>
                    {row.validation ? (
                      <Badge tone="ok">validated</Badge>
                    ) : (
                      <Badge tone="neutral">unknown</Badge>
                    )}
                  </td>
                  <td>
                    <a className="download-btn" href={artifactDownloadUrl(row.path)} download>
                      Download
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>
    </div>
  )
}

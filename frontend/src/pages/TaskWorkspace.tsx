import { useEffect, useRef, useState } from 'react'
import { artifactDownloadUrl, routeModel, runTask, uploadFile } from '../api/client'
import type { ChatResponse, RouteDecision } from '../api/types'
import { Badge, ErrorBanner, Panel, Spinner } from '../components/ui'
import ExecutionTrace from '../components/ExecutionTrace'
import './TaskWorkspace.css'

const IMAGE_EXTENSIONS = new Set(['.png', '.jpg', '.jpeg'])

interface UploadedDoc {
  fileId: string
  filename: string
  kind: 'document' | 'image'
  // Constructed from the backend's known save convention in
  // app/api/files.py (`UPLOAD_DIRECTORY / f"{file_id}{extension}"`).
  // /files/upload does not return a usable path today — only file_id —
  // so this is a bridge until that endpoint returns one directly.
  filePath: string
}

export default function TaskWorkspace() {
  const [message, setMessage] = useState('')
  const [doc, setDoc] = useState<UploadedDoc | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)

  const [routePreview, setRoutePreview] = useState<RouteDecision | null>(null)
  const [routeError, setRouteError] = useState<string | null>(null)
  const debounceRef = useRef<number | null>(null)

  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<ChatResponse | null>(null)
  const [runError, setRunError] = useState<string | null>(null)

  // Live routing preview: shows which model *would* be selected as the
  // user types, before they even submit. Debounced against GET /models/route.
  useEffect(() => {
    if (debounceRef.current) window.clearTimeout(debounceRef.current)

    if (message.trim().length < 4) {
      setRoutePreview(null)
      setRouteError(null)
      return
    }

    debounceRef.current = window.setTimeout(async () => {
      try {
        const decision = await routeModel(message)
        setRoutePreview(decision)
        setRouteError(null)
      } catch (err) {
        setRouteError(err instanceof Error ? err.message : 'Routing preview failed')
      }
    }, 400)

    return () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current)
    }
  }, [message])

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    setUploadError(null)

    try {
      const res = await uploadFile(file)
      if (res.status === 'error') {
        setUploadError(res.message)
        setDoc(null)
        return
      }

      const extension = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
      setDoc({
        fileId: res.file_id,
        filename: res.filename,
        kind: IMAGE_EXTENSIONS.has(extension) ? 'image' : 'document',
        filePath: `data/uploads/${res.file_id}${extension}`,
      })
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  async function handleRun() {
    if (!message.trim() || running) return

    setRunning(true)
    setRunError(null)
    setResult(null)

    try {
      const res = await runTask({
        message,
        file_path: doc?.kind === 'document' ? doc.filePath : null,
        has_image: doc?.kind === 'image',
        image_path: doc?.kind === 'image' ? doc.filePath : null,
      })
      setResult(res)
    } catch (err) {
      setRunError(err instanceof Error ? err.message : 'Task execution failed')
    } finally {
      setRunning(false)
    }
  }

  const artifactPath = result?.metadata?.artifact_path as string | undefined

  return (
    <div className="workspace">
      <div className="workspace-col">
        <Panel title="Task">
          <textarea
            className="workspace-input"
            placeholder="e.g. Summarize this inspection report and draft an approval note…"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={5}
          />

          <div className="workspace-file-row">
            <label className="file-input-label">
              {uploading ? <Spinner /> : '📎'} Attach document or image (PDF / DOCX / TXT / PNG / JPG)
              <input
                type="file"
                accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"
                onChange={handleFileChange}
                hidden
                disabled={uploading}
              />
            </label>
            {doc && (
              <Badge tone="accent">
                {doc.filename} ({doc.kind}){' '}
                <button className="chip-remove" onClick={() => setDoc(null)}>✕</button>
              </Badge>
            )}
          </div>
          {uploadError && <ErrorBanner message={uploadError} />}

          <button className="run-button" onClick={handleRun} disabled={running || !message.trim()}>
            {running ? <Spinner /> : '▶'} Run task
          </button>
        </Panel>

        <Panel title="Model routing">
          {routeError && <ErrorBanner message={routeError} />}
          {!routeError && !routePreview && (
            <p className="workspace-note">Start typing a task to see which local model would be selected.</p>
          )}
          {routePreview && (
            <div className="route-preview">
              <div className="route-model">{routePreview.selected_model}</div>
              <ul className="route-reasons">
                {routePreview.reason.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}
        </Panel>
      </div>

      <div className="workspace-col">
        <Panel title="Execution trace">
          {running && !result && (
            <div className="workspace-note">
              <Spinner /> Running task…
            </div>
          )}
          {runError && <ErrorBanner message={runError} />}
          {result && <ExecutionTrace events={result.events} />}
          {!running && !result && !runError && (
            <p className="workspace-note">Run a task to see live plan → act → observe → validate steps.</p>
          )}
        </Panel>

        {result && (
          <Panel
            title="Result"
            action={
              <Badge tone={result.status === 'success' ? 'ok' : 'err'}>{result.status}</Badge>
            }
          >
            {result.selected_model && (
              <p className="result-meta">
                Model used: <strong>{result.selected_model}</strong>
              </p>
            )}
            {result.response ? (
              <div className="result-response">{result.response}</div>
            ) : (
              <p className="workspace-note">No response text returned.</p>
            )}
            {result.error && <ErrorBanner message={result.error} />}

            {artifactPath && (
              <div className="artifact-row">
                <Badge tone="accent">Artifact generated</Badge>
                <code>{artifactPath}</code>
                <a className="download-link" href={artifactDownloadUrl(artifactPath)} download>
                  ⬇ Download
                </a>
              </div>
            )}
          </Panel>
        )}
      </div>
    </div>
  )
}

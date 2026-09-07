import { useEffect, useRef, useState, type DragEvent } from 'react'
import { artifactDownloadUrl, routeModel, runTask, uploadFile } from '../api/client'
import type { ChatResponse, RouteDecision } from '../api/types'
import { Badge, CodeTerminal, ErrorBanner, Panel, Spinner, StepperChecklist, type StepItem } from '../components/ui'
import ExecutionTrace from '../components/ExecutionTrace'
import './TaskWorkspace.css'

const IMAGE_EXTENSIONS = new Set(['.png', '.jpg', '.jpeg'])

interface UploadedDoc {
  fileId: string
  filename: string
  kind: 'document' | 'image'
  filePath: string
  size?: number
  previewUrl?: string
}

const DEMO_PRESETS = [
  {
    label: 'Inspection Approval Note (.docx)',
    desc: 'Extract findings from inspection report & compile approval note',
    prompt:
      'Review this inspection report for Heat Exchanger HX-204, extract the corrosion and wall-thinning findings, retrieve SOP maintenance limits from the local knowledge base, and draft an official approval note in Word (.docx) format.',
  },
  {
    label: 'Python Math & Sandbox Verification',
    desc: 'Calculate ASME Section VIII wall thickness in isolated sandbox',
    prompt:
      'Write a Python script to calculate the minimum required wall thickness of a refinery pressure vessel using ASME Section VIII formula: t = (P * R) / (S * E - 0.6 * P) + CA, where P = 2.5 MPa, R = 600 mm, S = 138 MPa, E = 1.0, and CA = 3.0 mm. Execute and verify the code in the local sandbox.',
  },
  {
    label: 'P&ID / Drawing Vision Review',
    desc: 'Analyze engineering schematic and valve loops',
    prompt:
      'Analyze the attached P&ID engineering schematic drawing. Identify the control valve loops, verify the pressure transmitter tags (PT-101 to PT-104), and check for safety relief line compliance.',
  },
  {
    label: 'Code Optimization & Auto-Routing',
    desc: 'Debug SCADA parser and optimize non-blocking implementation',
    prompt:
      'Debug this Python multiprocessing script that parses SCADA log files, identify why the worker thread pool deadlocks, and write an optimized non-blocking implementation.',
  },
]

export default function TaskWorkspace() {
  const [message, setMessage] = useState('')
  const [doc, setDoc] = useState<UploadedDoc | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)

  const [routePreview, setRoutePreview] = useState<RouteDecision | null>(null)
  const [routeError, setRouteError] = useState<string | null>(null)
  const debounceRef = useRef<number | null>(null)

  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<ChatResponse | null>(null)
  const [runError, setRunError] = useState<string | null>(null)

  // Live routing preview (debounced against GET /models/route)
  useEffect(() => {
    if (debounceRef.current) window.clearTimeout(debounceRef.current)

    debounceRef.current = window.setTimeout(async () => {
      if (message.trim().length < 4) {
        setRoutePreview(null)
        setRouteError(null)
        return
      }

      try {
        const decision = await routeModel(message, doc?.kind === 'image')
        setRoutePreview(decision)
        setRouteError(null)
      } catch (err) {
        setRouteError(err instanceof Error ? err.message : 'Routing preview failed')
      }
    }, 350)

    return () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current)
    }
  }, [message, doc])

  async function processSelectedFile(file: File) {
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
      const isImg = IMAGE_EXTENSIONS.has(extension)

      let previewUrl: string | undefined
      if (isImg) {
        previewUrl = URL.createObjectURL(file)
      }

      setDoc({
        fileId: res.file_id,
        filename: res.filename,
        kind: isImg ? 'image' : 'document',
        filePath: `data/uploads/${res.file_id}${extension}`,
        size: file.size,
        previewUrl,
      })
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) {
      processSelectedFile(file)
    }
    e.target.value = ''
  }

  function handleDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setIsDragging(true)
  }

  function handleDragLeave(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setIsDragging(false)
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file) {
      processSelectedFile(file)
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
      setRunError(
        err instanceof Error
          ? err.message
          : 'Task execution failed. Ensure the local backend server is active on port 8000.'
      )
    } finally {
      setRunning(false)
    }
  }

  // Derive agentic milestone steps from the task state
  const steps: StepItem[] = [
    {
      id: 'doc',
      label: 'Document Parsing & OCR Extraction',
      status: doc
        ? result
          ? 'completed'
          : running
            ? 'running'
            : 'pending'
        : 'skipped',
      detail: doc ? `Attached: ${doc.filename}` : 'No document attached',
    },
    {
      id: 'rag',
      label: 'Organizational SOP Knowledge Retrieval',
      status: result?.metadata?.plan
        ? 'completed'
        : running
          ? 'running'
          : 'pending',
      detail: 'Local vector store semantic search',
    },
    {
      id: 'model',
      label: 'Local LLM Reasoning & Synthesis',
      status: result?.response ? 'completed' : running ? 'running' : 'pending',
      detail: result?.selected_model ? `Executed on ${result.selected_model}` : 'Auto-selecting model',
    },
    {
      id: 'artifact',
      label: 'Deliverable File Generation & Validation',
      status: result?.metadata?.artifact_path
        ? 'completed'
        : result?.completed
          ? 'skipped'
          : running
            ? 'running'
            : 'pending',
      detail: result?.metadata?.artifact_path ? String(result.metadata.artifact_path) : 'Word / Excel / Code',
    },
  ]

  const artifactPath = result?.metadata?.artifact_path as string | undefined
  const artifactType = (result?.metadata?.artifact_type as string) || 'Document Deliverable'

  return (
    <div className="workspace-layout">
      {/* Left Column: Task Formulation */}
      <div className="workspace-main-col">
        {/* Preset scenario launcher */}
        <div className="presets-bar">
          <span className="presets-title">Industrial Workflow Presets:</span>
          <div className="presets-chips">
            {DEMO_PRESETS.map((preset, i) => (
              <button
                key={i}
                className="preset-chip"
                title={preset.desc}
                onClick={() => setMessage(preset.prompt)}
              >
                <span className="preset-chip-label">{preset.label}</span>
              </button>
            ))}
          </div>
        </div>

        <Panel title="Task Instruction">
          <textarea
            className="workspace-textarea"
            placeholder="Describe your task in natural language... (e.g. 'Analyze this inspection report, retrieve SOP limits, and generate an approval note in .docx format')"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={5}
          />

          {/* Drag & Drop File Upload Area */}
          <div
            className={`dropzone ${isDragging ? 'dropzone-active' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            {doc ? (
              <div className="uploaded-file-card">
                {doc.previewUrl ? (
                  <img src={doc.previewUrl} alt="Upload preview" className="file-preview-img" />
                ) : (
                  <div className="file-icon-placeholder">[FILE]</div>
                )}
                <div className="file-meta">
                  <span className="file-name">{doc.filename}</span>
                  <div className="file-tags">
                    <Badge tone="accent" size="sm">{doc.kind.toUpperCase()}</Badge>
                    {doc.size && <span className="file-size">{(doc.size / 1024).toFixed(1)} KB</span>}
                  </div>
                </div>
                <button className="remove-file-btn" onClick={() => setDoc(null)} title="Remove file">
                  ✕
                </button>
              </div>
            ) : (
              <label className="dropzone-label">
                <input
                  type="file"
                  accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"
                  onChange={handleFileChange}
                  hidden
                  disabled={uploading}
                />
                <div className="dropzone-text">
                  <strong>Click or Drag &amp; Drop confidential files here</strong>
                  <span className="dropzone-sub">Supports PDF, DOCX, TXT, Scanned Drawings &amp; Photos (PNG/JPG)</span>
                </div>
              </label>
            )}
          </div>

          {uploadError && (
            <ErrorBanner
              title="File Upload Notice"
              message={uploadError}
              tip="Check that the file format is supported and less than 50MB."
            />
          )}

          <div className="workspace-action-row">
            <button
              className="run-task-btn"
              onClick={handleRun}
              disabled={running || !message.trim()}
            >
              {running ? (
                <>
                  <Spinner size="sm" /> Orchestrating Multi-Step Agent...
                </>
              ) : (
                'Execute Sovereign Agent'
              )}
            </button>
          </div>
        </Panel>

        {/* Model Auto-Selection Preview */}
        <Panel title="Model Auto-Routing Decision">
          {routeError && <ErrorBanner message={routeError} />}
          {!routeError && !routePreview && (
            <p className="workspace-hint">Type a task above to see the on-premise model auto-selection engine in action.</p>
          )}
          {routePreview && (
            <div className="route-decision-card">
              <div className="route-decision-header">
                <div>
                  <span className="route-sub-label">AUTO-SELECTED LOCAL MODEL:</span>
                  <div className="route-model-name">{routePreview.selected_model}</div>
                </div>
                <Badge tone="accent" size="md" glow>Score {routePreview.score.toFixed(1)}</Badge>
              </div>

              <div className="route-reasons-box">
                <span className="reasons-heading">Selection Explanation:</span>
                <ul className="reasons-list">
                  {routePreview.reason.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </Panel>

        {/* Stepper Checklist */}
        <Panel title="Agent Workflow Progress">
          <StepperChecklist steps={steps} />
        </Panel>
      </div>

      {/* Right Column: Execution Trace & Final Deliverable */}
      <div className="workspace-side-col">
        {/* Results & Deliverable Card */}
        {result && (
          <Panel
            title="Task Result & Deliverables"
            action={<Badge tone={result.status === 'success' ? 'ok' : 'err'}>{result.status}</Badge>}
          >
            {result.selected_model && (
              <div className="result-model-badge">
                <span>Inference Engine:</span> <strong>{result.selected_model}</strong>
              </div>
            )}

            {/* Direct 1-Click Deliverable Download Card */}
            {artifactPath && (
              <div className="deliverable-card">
                <div className="deliverable-header">
                  <div className="deliverable-info">
                    <span className="deliverable-title">{artifactPath.split(/[/\\]/).pop()}</span>
                    <span className="deliverable-type">{artifactType}</span>
                  </div>
                  <Badge tone="ok" size="sm">✓ Validated</Badge>
                </div>
                <a
                  className="download-deliverable-btn"
                  href={artifactDownloadUrl(artifactPath)}
                  download
                >
                  Download Official Deliverable
                </a>
              </div>
            )}

            {/* Structured Response Text */}
            {result.response ? (
              <div className="result-text-box">
                <div className="result-text-content">{result.response}</div>
              </div>
            ) : (
              <p className="workspace-hint">No text output returned.</p>
            )}

            {/* Sandboxed Python Output Terminal */}
            {result.tool_results?.python ? (
              <CodeTerminal
                title="Python Sandbox Execution Output"
                code={String(
                  (result.tool_results.python as any)?.metadata?.code ||
                  '# Python script executed in isolated sandbox'
                )}
                output={String(
                  (result.tool_results.python as any)?.result ||
                  (result.tool_results.python as any)?.metadata?.stdout ||
                  ''
                )}
                error={
                  (result.tool_results.python as any)?.error ||
                  (result.tool_results.python as any)?.metadata?.stderr ||
                  null
                }
              />
            ) : null}

            {result.error && (
              <ErrorBanner
                title="Execution Encountered An Issue"
                message={result.error}
                tip="Check that all required local tools and models are online in the system."
              />
            )}
          </Panel>
        )}

        {runError && (
          <ErrorBanner
            title="Backend Execution Error"
            message={runError}
            tip="Verify that FastAPI backend is running locally on http://localhost:8000."
          />
        )}

        {/* Detailed Execution Trace */}
        <Panel title="Step-by-Step Execution Trace">
          {running && !result && (
            <div className="running-indicator">
              <Spinner size="md" /> <span>Agent is executing local tools and reasoning...</span>
            </div>
          )}
          {result && <ExecutionTrace events={result.events} />}
          {!running && !result && !runError && (
            <p className="workspace-hint">Run a task to see live multi-step planning, tool invocations, and observation traces.</p>
          )}
        </Panel>
      </div>
    </div>
  )
}

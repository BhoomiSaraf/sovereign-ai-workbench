import { useState, type DragEvent } from 'react'
import { searchKnowledge, uploadFile } from '../api/client'
import type { FileUploadResponse, KnowledgeSearchResponse } from '../api/types'
import { Badge, EmptyState, ErrorBanner, Panel, Spinner } from '../components/ui'
import './KnowledgeBase.css'

const KB_EXAMPLE_QUERIES = [
  'HX-204 heat exchanger maximum allowable corrosion thinning',
  'Centrifugal pump vibration inspection velocity threshold',
  'Pressure safety valve relief testing procedure',
  'Emergency shutdown interlock bypass authorization SOP',
]

export default function KnowledgeBase() {
  const [query, setQuery] = useState('')
  const [searching, setSearching] = useState(false)
  const [results, setResults] = useState<KnowledgeSearchResponse | null>(null)
  const [searchError, setSearchError] = useState<string | null>(null)

  const [uploading, setUploading] = useState(false)
  const [uploadLog, setUploadLog] = useState<FileUploadResponse[]>([])
  const [isDragging, setIsDragging] = useState(false)

  async function handleSearch(e?: React.FormEvent, customQuery?: string) {
    if (e) e.preventDefault()
    const targetQuery = customQuery || query
    if (!targetQuery.trim()) return

    setSearching(true)
    setSearchError(null)

    try {
      const res = await searchKnowledge(targetQuery)
      setResults(res)
    } catch (err) {
      setSearchError(
        err instanceof Error
          ? err.message
          : 'Semantic search failed. Verify local embeddings model (BGE-M3) is available.'
      )
    } finally {
      setSearching(false)
    }
  }

  function handlePresetClick(presetQuery: string) {
    setQuery(presetQuery)
    handleSearch(undefined, presetQuery)
  }

  async function processFiles(files: File[]) {
    if (files.length === 0) return
    setUploading(true)

    for (const file of files) {
      try {
        const res = await uploadFile(file)
        setUploadLog((prev) => [res, ...prev])
      } catch (err) {
        setUploadLog((prev) => [
          {
            status: 'error',
            message: err instanceof Error ? err.message : 'Ingestion failed',
            filename: file.name,
          },
          ...prev,
        ])
      }
    }

    setUploading(false)
  }

  function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? [])
    processFiles(files)
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
    const files = Array.from(e.dataTransfer.files ?? [])
    processFiles(files)
  }

  return (
    <div className="kb-container">
      <div className="kb-header">
        <div>
          <h1>Organizational Knowledge Base (Local RAG)</h1>
          <p className="kb-desc">
            All organizational SOPs, maintenance manuals, safety guidelines, and past correspondence are chunked and embedded on-premises via BGE-M3 with zero external connectivity.
          </p>
        </div>
        <div className="kb-spec-pill">
          <span className="spec-title">Vector DB Architecture:</span>
          <strong>Local Vector Store + BGE-M3</strong>
        </div>
      </div>

      <div className="kb-grid-layout">
        {/* Left: Ingestion */}
        <Panel title="Ingest Organizational Documents">
          <div
            className={`kb-dropzone ${isDragging ? 'kb-dropzone-active' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <label className="kb-dropzone-inner">
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                multiple
                hidden
                onChange={handleFileInput}
                disabled={uploading}
              />
              <div className="kb-dropzone-text">
                <strong>{uploading ? <Spinner size="md" /> : 'Drag & Drop SOPs or Manuals to Ingest'}</strong>
                <span className="kb-dropzone-sub">
                  Supports PDF, DOCX, TXT (Chunked and embedded locally into Vector DB)
                </span>
              </div>
            </label>
          </div>

          <div className="kb-log-section">
            <span className="kb-log-title">Recent Ingestion Events:</span>
            {uploadLog.length === 0 ? (
              <EmptyState message="No documents ingested this session." />
            ) : (
              <ul className="kb-upload-log">
                {uploadLog.map((entry, i) => (
                  <li key={i} className="kb-upload-item">
                    <Badge tone={entry.status === 'success' ? 'ok' : 'err'} size="sm">
                      {entry.status}
                    </Badge>
                    <span className="kb-upload-filename">{entry.filename ?? 'Document'}</span>
                    {entry.status === 'error' && (
                      <span className="kb-upload-msg">{entry.message}</span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </Panel>

        {/* Right: Semantic Search Tester */}
        <Panel title="Local Vector Semantic Search">
          <div className="kb-preset-queries">
            <span className="kb-preset-label">Sample Inspection Queries:</span>
            <div className="kb-preset-chips">
              {KB_EXAMPLE_QUERIES.map((q, i) => (
                <button
                  key={i}
                  type="button"
                  className="kb-preset-chip"
                  onClick={() => handlePresetClick(q)}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleSearch} className="kb-search-form">
            <div className="kb-search-input-group">
              <input
                type="text"
                className="kb-search-input"
                placeholder="e.g. pump vibration limit or heat exchanger inspection SOP..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <button
                type="submit"
                className="kb-search-btn"
                disabled={searching || !query.trim()}
              >
                {searching ? <Spinner size="sm" /> : 'Search RAG'}
              </button>
            </div>
          </form>

          {searchError && <ErrorBanner title="RAG Retrieval Notice" message={searchError} />}

          {results && results.count === 0 && (
            <EmptyState
              message="No sufficiently relevant organizational information found for this query in the local vector database."
            />
          )}

          {results && results.count > 0 && (
            <div className="kb-results-box">
              <div className="kb-results-header">
                <span className="kb-results-count">{results.count} Retrieved Knowledge Chunks</span>
                <span className="kb-results-engine">Embeddings: BGE-M3</span>
              </div>

              <ul className="kb-results-list">
                {results.results.map((r, i) => (
                  <li key={i} className="kb-result-card">
                    <div className="kb-result-top">
                      <span className="kb-result-source">{r.source.split(/[/\\]/).pop()}</span>
                      <Badge tone="accent" size="sm">
                        Similarity Score {(r.score * 100).toFixed(1)}%
                      </Badge>
                    </div>
                    <p className="kb-result-snippet">{r.text}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Panel>
      </div>
    </div>
  )
}

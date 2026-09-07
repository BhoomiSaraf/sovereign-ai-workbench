import { useState } from 'react'
import { searchKnowledge, uploadFile } from '../api/client'
import type { FileUploadResponse, KnowledgeSearchResponse } from '../api/types'
import { Badge, EmptyState, ErrorBanner, Panel, Spinner } from '../components/ui'
import './KnowledgeBase.css'

export default function KnowledgeBase() {
  const [query, setQuery] = useState('')
  const [searching, setSearching] = useState(false)
  const [results, setResults] = useState<KnowledgeSearchResponse | null>(null)
  const [searchError, setSearchError] = useState<string | null>(null)

  const [uploading, setUploading] = useState(false)
  const [uploadLog, setUploadLog] = useState<FileUploadResponse[]>([])

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    if (!query.trim()) return

    setSearching(true)
    setSearchError(null)

    try {
      const res = await searchKnowledge(query)
      setResults(res)
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : 'Search failed')
    } finally {
      setSearching(false)
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? [])
    if (files.length === 0) return

    setUploading(true)

    for (const file of files) {
      try {
        const res = await uploadFile(file)
        setUploadLog((prev) => [res, ...prev])
      } catch (err) {
        setUploadLog((prev) => [
          { status: 'error', message: err instanceof Error ? err.message : 'Upload failed', filename: file.name },
          ...prev,
        ])
      }
    }

    setUploading(false)
    e.target.value = ''
  }

  return (
    <div>
      <h1>Knowledge Base</h1>

      <div className="kb-grid">
        <Panel title="Ingest documents">
          <label className="kb-dropzone">
            {uploading ? <Spinner /> : '⬆'}
            <span>Drop or select PDF / DOCX / TXT files to ingest</span>
            <input type="file" accept=".pdf,.docx,.txt" multiple hidden onChange={handleUpload} disabled={uploading} />
          </label>

          {uploadLog.length === 0 ? (
            <EmptyState message="No documents ingested this session." />
          ) : (
            <ul className="kb-upload-log">
              {uploadLog.map((entry, i) => (
                <li key={i} className="kb-upload-item">
                  <Badge tone={entry.status === 'success' ? 'ok' : 'err'}>{entry.status}</Badge>
                  <span>{entry.filename ?? 'unknown file'}</span>
                  {entry.status === 'error' && <span className="kb-upload-msg">{entry.message}</span>}
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel title="Search organizational knowledge">
          <form onSubmit={handleSearch} className="kb-search-form">
            <input
              type="text"
              placeholder="e.g. pump vibration inspection procedure"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button type="submit" disabled={searching || !query.trim()}>
              {searching ? <Spinner /> : 'Search'}
            </button>
          </form>

          {searchError && <ErrorBanner message={searchError} />}

          {results && results.count === 0 && (
            <EmptyState message="No sufficiently relevant organizational information found." />
          )}

          {results && results.count > 0 && (
            <ul className="kb-results">
              {results.results.map((r, i) => (
                <li key={i} className="kb-result">
                  <div className="kb-result-header">
                    <span className="kb-result-source">{r.source}</span>
                    <Badge tone="accent">score {r.score.toFixed(3)}</Badge>
                  </div>
                  <p className="kb-result-text">{r.text}</p>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </div>
  )
}

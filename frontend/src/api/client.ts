import type {
  ApiError,
  AuditEventsResponse,
  ChatRequest,
  ChatResponse,
  FileUploadResponse,
  HealthResponse,
  KnowledgeSearchResponse,
  ModelsResponse,
  RouteDecision,
  TaskListResponse,
} from './types'

export class ApiRequestError extends Error implements ApiError {
  status?: number

  constructor(message: string, status?: number) {
    super(message)
    this.name = 'ApiRequestError'
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response

  try {
    res = await fetch(path, init)
  } catch {
    throw new ApiRequestError(
      'Could not reach the backend. Is the FastAPI server running on http://localhost:8000?',
    )
  }

  if (!res.ok) {
    let detail = res.statusText

    try {
      const body = await res.json()
      detail = body?.detail ?? body?.message ?? detail
    } catch {
      // response had no JSON body — fall back to statusText
    }

    throw new ApiRequestError(detail || `Request failed with ${res.status}`, res.status)
  }

  return (await res.json()) as T
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}

export function listModels(): Promise<ModelsResponse> {
  return request<ModelsResponse>('/models')
}

export function routeModel(task: string, hasImage = false): Promise<RouteDecision> {
  const params = new URLSearchParams({ task, has_image: String(hasImage) })
  return request<RouteDecision>(`/models/route?${params.toString()}`)
}

export function sendChat(body: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

// POST /tasks runs the same AgentOrchestrator workflow as /chat, but
// persists the result to the backend's in-memory TASK_STORE (so it shows
// up in GET /tasks — used by the Dashboard and Artifacts views). /chat
// does not persist anything, so the workspace runs tasks through here.
export function runTask(body: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>('/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function listTasks(): Promise<TaskListResponse> {
  return request<TaskListResponse>('/tasks')
}

export function searchKnowledge(query: string, topK = 5): Promise<KnowledgeSearchResponse> {
  const params = new URLSearchParams({ query, top_k: String(topK) })
  return request<KnowledgeSearchResponse>(`/knowledge/search?${params.toString()}`)
}

export async function uploadFile(file: File): Promise<FileUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  return request<FileUploadResponse>('/files/upload', {
    method: 'POST',
    body: formData,
  })
}

// GET /artifacts/download only accepts a bare filename (see
// app/api/artifacts.py) — strip any directory component from an
// artifact_path like "data/artifacts/foo.docx" before building the URL.
export function artifactDownloadUrl(artifactPath: string): string {
  const filename = artifactPath.split(/[/\\]/).pop() ?? artifactPath
  return `/artifacts/download?${new URLSearchParams({ filename }).toString()}`
}

export function getRecentAudit(limit = 100): Promise<AuditEventsResponse> {
  const params = new URLSearchParams({ limit: String(limit) })
  return request<AuditEventsResponse>(`/audit/recent?${params.toString()}`)
}

// Types mirror the real FastAPI response/request shapes in app/api/*.py.
// Keep these in sync with the backend — do not invent fields that the
// backend does not actually return.

export interface NetworkSnapshot {
  sovereign_mode: boolean
  external_network_allowed: boolean
  external_connections_detected: number
  message: string
}

export interface HealthResponse {
  status: string
  sovereign: boolean
  external_network_required: boolean
  network: NetworkSnapshot
}

export interface ModelInfo {
  name: string
  ollama_name: string
  capabilities: Record<string, number>
  modalities: string[]
  priority: number
}

export interface ModelsResponse {
  count: number
  models: ModelInfo[]
}

export interface TaskRequirementsDTO {
  capabilities: Record<string, number>
  modalities: string[]
  complexity: string
  rag_required: boolean
}

export interface RouteDecision {
  task: string
  has_image: boolean
  selected_model: string
  score: number
  matched_capabilities: string[]
  reason: string[]
  task_requirements: TaskRequirementsDTO
}

// Agent execution trace event — shape matches AgentState.add_event() in
// app/agent/state.py. `type` and `status` are the only guaranteed fields;
// everything else varies per event (tool, model, path, error, ...).
export interface AgentEvent {
  type: string
  status: string
  [key: string]: unknown
}

export interface ChatRequest {
  message: string
  file_path?: string | null
  has_image?: boolean
  image_path?: string | null
}

export interface ChatResponse {
  status: 'success' | 'error'
  task_id: string
  selected_model: string | null
  response: string | null
  completed: boolean
  error: string | null
  tool_results: Record<string, unknown>
  metadata: Record<string, unknown>
  events: AgentEvent[]
  routing_reason: string[]
  vision_context: string | null
}

export interface TaskListItem {
  task_id: string
  status?: string
  selected_model?: string | null
  response?: string | null
  completed?: boolean
  error?: string | null
  tool_results?: Record<string, unknown>
  metadata?: Record<string, unknown>
  events?: AgentEvent[]
  routing_reason?: string[]
  created_at?: string
  task_type?: string
  prompt?: string
  result?: string | null
}

export interface TaskListResponse {
  count: number
  tasks: TaskListItem[]
}

export interface FileUploadSuccess {
  status: 'success'
  file_id: string
  filename: string
  ingestion: unknown
}

export interface FileUploadError {
  status: 'error'
  file_id?: string
  filename?: string
  message: string
}

export type FileUploadResponse = FileUploadSuccess | FileUploadError

export interface KnowledgeResult {
  text: string
  source: string
  score: number
  metadata: Record<string, unknown>
}

// Matches AuditLogger.record() in app/security/audit.py — read via
// GET /audit/recent.
export interface AuditEvent {
  timestamp: string
  event_type: string
  status: string
  task_id: string | null
  details: Record<string, unknown>
}

export interface AuditEventsResponse {
  count: number
  events: AuditEvent[]
}

export interface KnowledgeSearchResponse {
  query: string
  count: number
  results: KnowledgeResult[]
}

// Structured client-side error for any failed API call, so the UI can
// render a consistent error state instead of an unhandled exception.
export interface ApiError {
  message: string
  status?: number
}

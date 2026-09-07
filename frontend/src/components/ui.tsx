import { type ReactNode, useState } from 'react'
import './ui.css'

export function Panel({
  title,
  subtitle,
  action,
  children,
  className = '',
}: {
  title?: string
  subtitle?: string
  action?: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <section className={`panel ${className}`}>
      {(title || action) && (
        <div className="panel-header">
          <div className="panel-title-group">
            <div>
              {title && <h3>{title}</h3>}
              {subtitle && <p className="panel-subtitle">{subtitle}</p>}
            </div>
          </div>
          {action && <div className="panel-action">{action}</div>}
        </div>
      )}
      <div className="panel-body">{children}</div>
    </section>
  )
}

export function EmptyState({
  message,
  action,
}: {
  message: string
  action?: ReactNode
}) {
  return (
    <div className="empty-state">
      <p className="empty-state-message">{message}</p>
      {action && <div className="empty-state-action">{action}</div>}
    </div>
  )
}

export function ErrorBanner({
  title = 'Execution Notice',
  message,
  tip,
}: {
  title?: string
  message: string
  tip?: string
}) {
  return (
    <div className="error-banner">
      <div className="error-banner-indicator">!</div>
      <div className="error-banner-content">
        <strong className="error-banner-title">{title}</strong>
        <p className="error-banner-msg">{message}</p>
        {tip && <div className="error-banner-tip"><strong>Note:</strong> {tip}</div>}
      </div>
    </div>
  )
}

export function Spinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  return <span className={`spinner spinner-${size}`} aria-label="Loading" />
}

export function Badge({
  tone = 'neutral',
  size = 'md',
  glow = false,
  children,
}: {
  tone?: 'neutral' | 'ok' | 'warn' | 'err' | 'accent' | 'purple' | 'info'
  size?: 'sm' | 'md'
  glow?: boolean
  children: ReactNode
}) {
  return (
    <span className={`badge badge-${tone} badge-${size} ${glow ? 'badge-glow' : ''}`}>
      {children}
    </span>
  )
}

export function MetricTile({
  label,
  value,
  detail,
  status = 'neutral',
}: {
  label: string
  value: string | number | ReactNode
  detail?: string
  status?: 'ok' | 'warn' | 'err' | 'info' | 'neutral'
}) {
  return (
    <div className={`metric-tile metric-tile-${status}`}>
      <div className="metric-tile-header">
        <span className="metric-tile-label">{label}</span>
      </div>
      <div className="metric-tile-value">{value}</div>
      {detail && <div className="metric-tile-detail">{detail}</div>}
    </div>
  )
}

export function CodeTerminal({
  code,
  language = 'python',
  title = 'Sandboxed Script',
  output,
  error,
}: {
  code: string
  language?: string
  title?: string
  output?: string | null
  error?: string | null
}) {
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="code-terminal">
      <div className="code-terminal-header">
        <div className="code-terminal-dots">
          <span className="dot dot-red" />
          <span className="dot dot-yellow" />
          <span className="dot dot-green" />
        </div>
        <span className="code-terminal-title">{title} ({language})</span>
        <button className="code-terminal-copy" onClick={handleCopy}>
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre className="code-terminal-body">
        <code>{code}</code>
      </pre>
      {(output || error) && (
        <div className="code-terminal-output">
          <div className="output-label">
            {error ? 'Execution Output (Errors Detected):' : 'Execution Result (Stdout):'}
          </div>
          <pre className={`output-text ${error ? 'output-err' : 'output-ok'}`}>
            {error ? error : output}
          </pre>
        </div>
      )}
    </div>
  )
}

export interface StepItem {
  id: string
  label: string
  status: 'completed' | 'running' | 'pending' | 'failed' | 'skipped'
  detail?: string
}

export function StepperChecklist({ steps }: { steps: StepItem[] }) {
  return (
    <div className="stepper-checklist">
      <div className="stepper-title">Agent Workflow Milestones</div>
      <ul className="stepper-list">
        {steps.map((step) => {
          const isDone = step.status === 'completed'
          const isRunning = step.status === 'running'
          const isFailed = step.status === 'failed'

          return (
            <li key={step.id} className={`stepper-item stepper-${step.status}`}>
              <span className="stepper-bullet">
                {isDone && '✓'}
                {isRunning && <Spinner size="sm" />}
                {isFailed && '✕'}
                {!isDone && !isRunning && !isFailed && '○'}
              </span>
              <div className="stepper-content">
                <span className="stepper-label">{step.label}</span>
                {step.detail && <span className="stepper-detail">{step.detail}</span>}
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

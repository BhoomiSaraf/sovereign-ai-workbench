import type { ReactNode } from 'react'
import './ui.css'

export function Panel({
  title,
  action,
  children,
}: {
  title?: string
  action?: ReactNode
  children: ReactNode
}) {
  return (
    <section className="panel">
      {(title || action) && (
        <div className="panel-header">
          {title && <h3>{title}</h3>}
          {action}
        </div>
      )}
      <div className="panel-body">{children}</div>
    </section>
  )
}

export function EmptyState({ message }: { message: string }) {
  return <div className="empty-state">{message}</div>
}

export function ErrorBanner({ message }: { message: string }) {
  return <div className="error-banner">⚠ {message}</div>
}

export function Spinner() {
  return <span className="spinner" aria-label="Loading" />
}

export function Badge({
  tone = 'neutral',
  children,
}: {
  tone?: 'neutral' | 'ok' | 'warn' | 'err' | 'accent'
  children: ReactNode
}) {
  return <span className={`badge badge-${tone}`}>{children}</span>
}

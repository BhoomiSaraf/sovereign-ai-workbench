import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { useHealth } from '../hooks/useHealth'
import './AppShell.css'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/workspace', label: 'Task Workspace' },
  { to: '/knowledge', label: 'Knowledge Base' },
  { to: '/models', label: 'Models' },
  { to: '/artifacts', label: 'Artifacts' },
  { to: '/security', label: 'Security Monitor' },
]

export default function AppShell({ children }: { children: ReactNode }) {
  const { health, error } = useHealth()

  const sovereign = health?.network?.sovereign_mode ?? null
  const externalCalls = health?.network?.external_connections_detected

  return (
    <div className="shell">
      <aside className="shell-sidebar">
        <div className="shell-brand">
          <span className="shell-brand-mark" />
          Sovereign AI Workbench
        </div>
        <nav className="shell-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => 'shell-nav-link' + (isActive ? ' active' : '')}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="shell-main">
        <header className="shell-topbar">
          <div className="shell-topbar-status">
            <span className={`dot ${error ? 'dot-err' : sovereign ? 'dot-ok' : 'dot-warn'}`} />
            {error
              ? 'Backend unreachable'
              : sovereign === null
                ? 'Checking sovereignty status…'
                : sovereign
                  ? 'AIR-GAPPED / LOCAL'
                  : 'External network permitted'}
          </div>
          <div className="shell-topbar-metric">
            External calls:&nbsp;
            <strong className={externalCalls ? 'text-err' : 'text-ok'}>
              {externalCalls ?? '—'}
            </strong>
          </div>
        </header>

        <main className="shell-content">{children}</main>
      </div>
    </div>
  )
}

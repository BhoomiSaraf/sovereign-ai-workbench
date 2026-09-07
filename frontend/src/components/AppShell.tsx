import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { useHealth } from '../hooks/useHealth'
import { useTheme } from '../hooks/useTheme'
import { Badge } from './ui'
import { ThemeSwitch } from './ThemeSwitch'
import './AppShell.css'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/workspace', label: 'Task Workspace' },
  { to: '/knowledge', label: 'Knowledge Base' },
  { to: '/models', label: 'Models & Routing' },
  { to: '/artifacts', label: 'Artifacts & Docs' },
  { to: '/security', label: 'Sovereignty Monitor' },
]

export default function AppShell({ children }: { children: ReactNode }) {
  const { health, error, loading } = useHealth()
  const { theme, toggleTheme } = useTheme()

  const sovereign = health?.network?.sovereign_mode ?? true
  const externalCalls = health?.network?.external_connections_detected ?? 0

  return (
    <div className="shell">
      <aside className="shell-sidebar">
        <div className="shell-brand">
          <div className="brand-logo">
            <span className="brand-mark" />
            <div className="brand-text">
              <span className="brand-title">SOVEREIGN AI</span>
              <span className="brand-subtitle">INDUSTRIAL WORKBENCH</span>
            </div>
          </div>
          <Badge tone="accent" size="sm" glow>AIR-GAPPED</Badge>
        </div>

        <nav className="shell-nav">
          <div className="nav-section-title">NAVIGATION</div>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => 'shell-nav-link' + (isActive ? ' active' : '')}
            >
              <span className="nav-bullet" />
              <span className="nav-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="shell-sidebar-footer">
          <div className="system-pill">
            <div className="system-pill-header">
              <span className="dot dot-ok" />
              <span className="system-mode-text">Local GPU Engine</span>
            </div>
            <span className="system-spec">Target: 8GB VRAM (Qwen / BGE)</span>
          </div>
        </div>
      </aside>

      <div className="shell-main">
        <header className="shell-topbar">
          <div className="shell-topbar-left">
            <div className={`airgap-badge ${error ? 'airgap-err' : sovereign ? 'airgap-ok' : 'airgap-warn'}`}>
              <span className={`status-pulse ${error ? 'pulse-red' : sovereign ? 'pulse-green' : 'pulse-amber'}`} />
              <span className="airgap-text">
                {error
                  ? 'BACKEND OFFLINE'
                  : loading && !health
                    ? 'VERIFYING AIR-GAP…'
                    : sovereign
                      ? 'AIR-GAPPED / ZERO-EGRESS'
                      : 'EXTERNAL NETWORK PERMITTED'}
              </span>
            </div>
          </div>

          <div className="shell-topbar-right">
            <div className="topbar-metric-pill">
              <span className="metric-label">External Egress:</span>
              <strong className={externalCalls > 0 ? 'text-err' : 'text-ok'}>
                {externalCalls} Calls
              </strong>
            </div>

            <div className="topbar-metric-pill">
              <span className="metric-label">Inference:</span>
              <strong className="text-ok">100% On-Premise</strong>
            </div>

            <ThemeSwitch theme={theme} onToggle={toggleTheme} />
          </div>
        </header>

        <main className="shell-content">{children}</main>
      </div>
    </div>
  )
}

import type { Theme } from '../hooks/useTheme'
import './ThemeSwitch.css'

interface ThemeSwitchProps {
  theme: Theme
  onToggle: () => void
}

export function ThemeSwitch({ theme, onToggle }: ThemeSwitchProps) {
  const isDark = theme === 'dark'

  return (
    <button
      type="button"
      className={`theme-capsule-btn ${isDark ? 'capsule-dark' : 'capsule-light'}`}
      onClick={onToggle}
      role="switch"
      aria-checked={isDark}
      aria-label={`Switch to ${isDark ? 'Light' : 'Dark'} Mode`}
      title={`Switch to ${isDark ? 'Light' : 'Dark'} Mode`}
    >
      <div className="capsule-track">
        {isDark ? (
          <>
            <div className="capsule-knob" aria-hidden="true">
              <svg
                className="knob-icon moon-icon"
                viewBox="0 0 24 24"
                fill="#0f141c"
                xmlns="http://www.w3.org/2000/svg"
              >
                {/* Crescent Moon */}
                <path d="M12.3 2a10 10 0 0 0-.19 14 10 10 0 0 0 11.64 2.15 10 10 0 1 1-11.45-16.15z" />
                {/* Star 1 */}
                <path d="M19 3l.6 1.3 1.4.6-1.4.6-.6 1.3-.6-1.3-1.4-.6 1.4-.6z" />
                {/* Star 2 */}
                <path d="M21.5 8.5l.4.9.9.4-.9.4-.4.9-.4-.9-.9-.4.9-.4z" />
                {/* Star 3 */}
                <path d="M16 8l.3.7.7.3-.7.3-.3.7-.3-.7-.7-.3.7-.3z" />
              </svg>
            </div>
            <div className="capsule-text-group" aria-hidden="true">
              <span className="capsule-text-main">DARK</span>
              <span className="capsule-text-sub">MODE</span>
            </div>
          </>
        ) : (
          <>
            <div className="capsule-text-group" aria-hidden="true">
              <span className="capsule-text-main">LIGHT</span>
              <span className="capsule-text-sub">MODE</span>
            </div>
            <div className="capsule-knob" aria-hidden="true">
              <svg
                className="knob-icon sun-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#475569"
                strokeWidth="2.4"
                strokeLinecap="round"
                strokeLinejoin="round"
                xmlns="http://www.w3.org/2000/svg"
              >
                {/* Sun Center */}
                <circle cx="12" cy="12" r="4.5" fill="#475569" />
                {/* 8 Radial Rays */}
                <line x1="12" y1="2" x2="12" y2="4.5" />
                <line x1="12" y1="19.5" x2="12" y2="22" />
                <line x1="2" y1="12" x2="4.5" y2="12" />
                <line x1="19.5" y1="12" x2="22" y2="12" />
                <line x1="4.93" y1="4.93" x2="6.7" y2="6.7" />
                <line x1="17.3" y1="17.3" x2="19.07" y2="19.07" />
                <line x1="4.93" y1="19.07" x2="6.7" y2="17.3" />
                <line x1="17.3" y1="6.7" x2="19.07" y2="4.93" />
              </svg>
            </div>
          </>
        )}
      </div>
    </button>
  )
}

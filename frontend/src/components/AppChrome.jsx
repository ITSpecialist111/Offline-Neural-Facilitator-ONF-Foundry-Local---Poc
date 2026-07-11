import {
  Archive,
  ChevronRight,
  Database,
  Download,
  Gauge,
  Menu,
  Moon,
  Play,
  Radio,
  ShieldCheck,
  Sparkles,
  Sun,
  X,
} from 'lucide-react'

function Brand() {
  return (
    <div className="brand" aria-label="Offline Neural Facilitator">
      <div className="brand-mark" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <div>
        <strong>ONF</strong>
        <span>Local meeting intelligence</span>
      </div>
    </div>
  )
}

export function AppHeader({ connection, theme, onToggleTheme, onExport, onToggleNavigation }) {
  const connectionText = connection === 'online'
    ? 'Local service connected'
    : connection === 'connecting'
      ? 'Connecting locally'
      : 'Local service unavailable'

  return (
    <header className="app-header">
      <button
        className="icon-button mobile-menu-button"
        type="button"
        aria-label="Open workspace navigation"
        onClick={onToggleNavigation}
      >
        <Menu size={20} />
      </button>
      <Brand />
      <div className="header-status" role="status">
        <span className={`connection-dot is-${connection}`} aria-hidden="true" />
        <span>{connectionText}</span>
      </div>
      <div className="header-actions">
        <span className="privacy-label"><ShieldCheck size={16} /> Stays on this device</span>
        <button
          className="icon-button"
          type="button"
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
          onClick={onToggleTheme}
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
        <button className="button button-secondary compact" type="button" onClick={onExport}>
          <Download size={16} />
          <span>Export</span>
        </button>
      </div>
    </header>
  )
}

function NavigationButton({ icon: Icon, label, detail, onClick, active = false }) {
  return (
    <button
      className={`navigation-item${active ? ' is-active' : ''}`}
      type="button"
      onClick={onClick}
      aria-current={active ? 'page' : undefined}
    >
      <Icon size={18} />
      <span>
        <strong>{label}</strong>
        {detail && <small>{detail}</small>}
      </span>
      <ChevronRight size={15} className="navigation-chevron" />
    </button>
  )
}

function CapabilityState({ label, status }) {
  const ready = status === 'ready' || status === 'local'
  const display = ready ? 'Ready' : status === 'loading' ? 'Loading' : 'Standby'
  return (
    <div className="capability-row">
      <span>{label}</span>
      <span className={`capability-state${ready ? ' is-ready' : ''}`}>{display}</span>
    </div>
  )
}

export function Sidebar({
  capabilities,
  mobileOpen,
  onClose,
  onOpenVault,
  onOpenSystem,
  onOpenOutcomes,
  onRunDemo,
  demoRunning,
}) {
  return (
    <>
      <button
        className={`sidebar-scrim${mobileOpen ? ' is-visible' : ''}`}
        type="button"
        aria-label="Close workspace navigation"
        onClick={onClose}
      />
      <aside className={`sidebar${mobileOpen ? ' is-open' : ''}`} aria-label="Workspace navigation">
        <div className="sidebar-mobile-header">
          <Brand />
          <button className="icon-button" type="button" aria-label="Close navigation" onClick={onClose}>
            <X size={19} />
          </button>
        </div>

        <div className="workspace-label">
          <span>Private workspace</span>
          <strong>Facilitation room</strong>
        </div>

        <nav className="navigation-list">
          <NavigationButton icon={Radio} label="Live workspace" detail="Capture and guide" active onClick={onClose} />
          <NavigationButton icon={Archive} label="Outcomes" detail="Decisions and actions" onClick={onOpenOutcomes} />
          <NavigationButton icon={Database} label="Knowledge vault" detail="Local evidence" onClick={onOpenVault} />
          <NavigationButton icon={Gauge} label="Capabilities" detail="Models, audio and skills" onClick={onOpenSystem} />
        </nav>

        <section className="showcase-card" aria-labelledby="showcase-title">
          <div className="showcase-icon"><Sparkles size={18} /></div>
          <div>
            <span className="eyebrow">Presenter mode</span>
            <h2 id="showcase-title">Show the complete loop</h2>
            <p>Run a fictional hospital ransomware decision room with cited evidence, specialist skills, and accountable outcomes.</p>
          </div>
          <button className="button button-primary full-width" type="button" onClick={onRunDemo} disabled={demoRunning}>
            <Play size={16} fill="currentColor" />
            {demoRunning ? 'Scenario running…' : 'Run showcase'}
          </button>
        </section>

        <section className="capabilities-card" aria-labelledby="local-stack-title">
          <div className="section-heading compact-heading">
            <div>
              <span className="eyebrow">Local stack</span>
              <h2 id="local-stack-title">Capability state</h2>
            </div>
            <ShieldCheck size={18} />
          </div>
          <CapabilityState label="Foundry Local" status={capabilities.foundry?.status} />
          <CapabilityState label="Knowledge" status={capabilities.knowledge?.status} />
          <CapabilityState label="Transcription" status={capabilities.transcription?.status} />
          <button className="text-button" type="button" onClick={onOpenSystem}>View system detail <ChevronRight size={14} /></button>
        </section>
      </aside>
    </>
  )
}
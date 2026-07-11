import {
  AlertTriangle,
  BookOpenText,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  ClipboardCheck,
  Lightbulb,
  Scale,
  ShieldAlert,
  Sparkles,
  UserRound,
  Volume2,
} from 'lucide-react'

const TABS = [
  { id: 'guidance', label: 'Guidance', icon: Lightbulb },
  { id: 'decisions', label: 'Decisions', icon: Scale },
  { id: 'actions', label: 'Actions', icon: ClipboardCheck },
  { id: 'risks', label: 'Risks', icon: ShieldAlert },
]

const INSIGHT_ICONS = {
  knowledge: BookOpenText,
  risk: AlertTriangle,
  skill: Sparkles,
  pace: CircleDot,
  facilitation: Lightbulb,
}

function EmptyFeed({ type }) {
  const copy = {
    guidance: ['The facilitator is listening', 'Evidence, pacing notes and useful interventions will appear here.'],
    decisions: ['No decision recorded yet', 'Say “we decided…” or run the showcase to capture one.'],
    actions: ['No owned actions yet', 'Explicit commitments will be separated from the transcript.'],
    risks: ['No material risk detected', 'Alignment gaps and unresolved constraints will surface here.'],
  }[type]

  return (
    <div className="empty-feed">
      <CheckCircle2 size={24} />
      <strong>{copy[0]}</strong>
      <p>{copy[1]}</p>
    </div>
  )
}

function GuidanceCard({ insight, onSpeak }) {
  const Icon = INSIGHT_ICONS[insight.kind] || Lightbulb
  return (
    <article className={`guidance-card severity-${insight.severity || 'info'}`}>
      <header>
        <span className="guidance-icon"><Icon size={16} /></span>
        <div>
          <span>{insight.kind}</span>
          <strong>{insight.title}</strong>
        </div>
        <button className="quiet-icon-button" type="button" aria-label={`Read ${insight.title} aloud`} onClick={() => onSpeak(insight.text)}>
          <Volume2 size={16} />
        </button>
      </header>
      <p>{insight.text}</p>
      <footer>
        <span>{insight.source || 'facilitator'}</span>
        {insight.citation && <span className="citation"><BookOpenText size={13} /> {insight.citation}</span>}
      </footer>
    </article>
  )
}

function DecisionCard({ decision, index }) {
  return (
    <article className="outcome-card decision-card">
      <div className="outcome-index">{String(index + 1).padStart(2, '0')}</div>
      <div>
        <span className="eyebrow">Decision captured</span>
        <p>{decision.text}</p>
        {decision.rationale && <small>{decision.rationale}</small>}
      </div>
    </article>
  )
}

function ActionCard({ action, index }) {
  return (
    <article className="outcome-card action-card">
      <span className="action-check" aria-hidden="true">{index + 1}</span>
      <div>
        <p>{action.text}</p>
        <footer>
          <span><UserRound size={13} /> {action.owner}</span>
          <span>{action.due}</span>
        </footer>
      </div>
    </article>
  )
}

export function IntelligencePanel({ state, activeTab, onTabChange, onSpeak, speaking }) {
  const guidance = [...state.insights].reverse()

  return (
    <aside className="intelligence-panel" id="outcomes-panel" aria-label="Facilitator intelligence">
      <header className="intelligence-heading">
        <div>
          <span className="eyebrow">Quiet intervention</span>
          <h2>Facilitator feed</h2>
        </div>
        <div className="intelligence-count" aria-label={`${state.insights.length} insights`}>
          {state.insights.length}
        </div>
      </header>

      <div className="intelligence-tabs" role="tablist" aria-label="Facilitator feed views">
        {TABS.map(({ id, label, icon: Icon }) => {
          const count = id === 'guidance'
            ? state.insights.length
            : id === 'decisions'
              ? state.decisions.length
              : id === 'actions'
                ? state.actions.length
                : state.risks.length
          return (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={activeTab === id}
              className={activeTab === id ? 'is-active' : ''}
              onClick={() => onTabChange(id)}
            >
              <Icon size={15} />
              <span>{label}</span>
              {count > 0 && <small>{count}</small>}
            </button>
          )
        })}
      </div>

      <div className="intelligence-scroll" role="tabpanel">
        {activeTab === 'guidance' && (
          guidance.length ? guidance.map((insight) => (
            <GuidanceCard key={insight.id} insight={insight} onSpeak={onSpeak} />
          )) : <EmptyFeed type="guidance" />
        )}

        {activeTab === 'decisions' && (
          state.decisions.length ? state.decisions.map((decision, index) => (
            <DecisionCard key={decision.id} decision={decision} index={index} />
          )) : <EmptyFeed type="decisions" />
        )}

        {activeTab === 'actions' && (
          state.actions.length ? state.actions.map((action, index) => (
            <ActionCard key={action.id} action={action} index={index} />
          )) : <EmptyFeed type="actions" />
        )}

        {activeTab === 'risks' && (
          state.risks.length ? [...state.risks].reverse().map((risk) => (
            <GuidanceCard key={risk.id} insight={risk} onSpeak={onSpeak} />
          )) : <EmptyFeed type="risks" />
        )}
      </div>

      <footer className="intelligence-footer">
        <span><Sparkles size={14} /> {speaking ? 'Generating local speech…' : 'Intervenes only when useful'}</span>
        <ChevronRight size={14} />
      </footer>
    </aside>
  )
}
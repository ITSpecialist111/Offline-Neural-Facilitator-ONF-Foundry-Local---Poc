import { useEffect, useMemo, useRef, useState } from 'react'
import {
  ArrowUp,
  BrainCircuit,
  CircleStop,
  Clock3,
  FileCheck2,
  Lightbulb,
  Mic,
  Plus,
  Radio,
  Sparkles,
  Users,
} from 'lucide-react'

function formatTime(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit' }).format(new Date(value))
}

function initials(name = 'Speaker') {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()
}

function TranscriptEntry({ message, newest }) {
  const isFacilitator = message.role === 'assistant'
  return (
    <article className={`transcript-entry${isFacilitator ? ' is-facilitator' : ''}${newest ? ' is-newest' : ''}`}>
      <div className="speaker-avatar" aria-hidden="true">
        {isFacilitator ? <Sparkles size={17} /> : initials(message.speaker)}
      </div>
      <div className="transcript-copy">
        <header>
          <strong>{message.speaker || (isFacilitator ? 'Facilitator' : 'Speaker')}</strong>
          <span>{isFacilitator ? 'Local facilitator' : formatTime(message.timestamp)}</span>
        </header>
        <p>{message.content}</p>
        {message.skills_triggered?.length > 0 && (
          <div className="inline-tags">
            {message.skills_triggered.map((skill) => <span key={skill}>{skill}</span>)}
          </div>
        )}
      </div>
    </article>
  )
}

function EmptyTranscript({ onRunDemo, onRecord, canRecord }) {
  return (
    <div className="empty-transcript">
      <div className="empty-visual" aria-hidden="true">
        <span className="signal-line line-one" />
        <span className="signal-line line-two" />
        <span className="signal-line line-three" />
        <div><BrainCircuit size={28} /></div>
      </div>
      <span className="eyebrow">Ready when the room is</span>
      <h2>Turn conversation into clear decisions.</h2>
      <p>Capture a real meeting, or run the guided showcase to see local evidence, conflict detection and action ownership working together.</p>
      <div className="empty-actions">
        <button className="button button-primary" type="button" onClick={onRecord} disabled={!canRecord}>
          <Mic size={17} /> Start listening
        </button>
        <button className="button button-secondary" type="button" onClick={onRunDemo}>
          <Sparkles size={17} /> Run showcase
        </button>
      </div>
    </div>
  )
}

function Metric({ icon: Icon, label, value, detail }) {
  return (
    <div className="metric">
      <Icon size={18} />
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
    </div>
  )
}

function ListeningSignal({ active }) {
  return (
    <div className={`listening-signal${active ? ' is-active' : ''}`} aria-hidden="true">
      {[0, 1, 2, 3, 4].map((bar) => <span key={bar} />)}
    </div>
  )
}

export function TranscriptWorkspace({
  state,
  connection,
  isRecording,
  segmentsSent,
  onToggleRecording,
  onRunDemo,
  onAsk,
  onNewSession,
  queryBusy,
}) {
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState('reflex')
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, [state.transcript.length])

  const metrics = useMemo(() => {
    const words = state.transcript.reduce((sum, message) => sum + message.content.split(/\s+/).length, 0)
    const alignment = Math.max(42, Math.min(96, 72 + state.actions.length * 4 + state.decisions.length * 5 - state.risks.length * 3))
    const speakers = new Set(state.transcript.filter((message) => message.role === 'participant').map((message) => message.speaker)).size
    return { words, alignment, speakers }
  }, [state.actions.length, state.decisions.length, state.risks.length, state.transcript])

  const submitQuery = async (event) => {
    event.preventDefault()
    const value = query.trim()
    if (!value || queryBusy) return
    setQuery('')
    await onAsk(value, mode)
  }

  const sessionStatus = isRecording
    ? `Listening · ${segmentsSent} segment${segmentsSent === 1 ? '' : 's'} secured`
    : state.session.status === 'showcase'
      ? 'Showcase in progress'
      : 'Workspace ready'

  return (
    <main className="workspace" id="main-content">
      <section className="session-overview" aria-labelledby="session-title">
        <div className="session-title-block">
          <div className="session-kicker">
            <span className={`live-indicator${isRecording ? ' is-recording' : ''}`}><Radio size={13} /> {sessionStatus}</span>
            <span>{state.session.id}</span>
            {state.session.topic_source === 'conversation' && (
              <span className="auto-title-badge"><Sparkles size={11} /> Auto-titled locally</span>
            )}
          </div>
          <h1 id="session-title">{state.session.topic}</h1>
          <p>A private facilitation workspace for evidence, alignment and accountable outcomes.</p>
        </div>
        <div className="session-actions">
          <button className="button button-secondary compact" type="button" onClick={onNewSession}>
            <Plus size={16} /> New session
          </button>
        </div>
      </section>

      <section className="metrics-strip" aria-label="Session measures">
        <Metric icon={Lightbulb} label="Alignment" value={`${metrics.alignment}%`} detail={state.risks.length ? (state.decisions.length ? 'Risk controlled' : 'Needs attention') : 'On track'} />
        <Metric icon={Users} label="Voices" value={metrics.speakers || '—'} detail={`${state.transcript.length} captured turns`} />
        <Metric icon={FileCheck2} label="Outcomes" value={state.actions.length + state.decisions.length} detail={`${state.actions.length} actions · ${state.decisions.length} ${state.decisions.length === 1 ? 'decision' : 'decisions'}`} />
        <Metric icon={Clock3} label="Context" value={metrics.words} detail="Local transcript words" />
      </section>

      <section className="transcript-card" aria-labelledby="transcript-heading">
        <header className="panel-header">
          <div>
            <span className="eyebrow">Live record</span>
            <h2 id="transcript-heading">Conversation</h2>
          </div>
          <div className="panel-header-meta">
            <ListeningSignal active={isRecording} />
            <span>{isRecording ? 'Capturing locally' : 'Microphone paused'}</span>
          </div>
        </header>

        <div className="transcript-scroll" aria-live="polite" aria-relevant="additions">
          {state.transcript.length === 0 ? (
            <EmptyTranscript
              onRunDemo={onRunDemo}
              onRecord={onToggleRecording}
              canRecord={connection === 'online'}
            />
          ) : (
            <div className="transcript-list">
              {state.transcript.map((message, index) => (
                <TranscriptEntry
                  key={message.id}
                  message={message}
                  newest={index === state.transcript.length - 1}
                />
              ))}
              <div ref={endRef} />
            </div>
          )}
        </div>
      </section>

      <section className="control-dock" aria-label="Session controls">
        <button
          className={`record-button${isRecording ? ' is-recording' : ''}`}
          type="button"
          onClick={onToggleRecording}
          disabled={connection !== 'online'}
          aria-pressed={isRecording}
          aria-label={isRecording ? 'Stop microphone capture' : 'Start microphone capture'}
        >
          {isRecording ? <CircleStop size={22} fill="currentColor" /> : <Mic size={22} />}
        </button>

        <form className="facilitator-composer" onSubmit={submitQuery}>
          <div className="composer-topline">
            <label htmlFor="facilitator-query">Ask the facilitator</label>
            <div className="mode-switch" aria-label="Reasoning mode">
              <button type="button" className={mode === 'reflex' ? 'is-active' : ''} onClick={() => setMode('reflex')} aria-pressed={mode === 'reflex'}>Reflex</button>
              <button type="button" className={mode === 'reason' ? 'is-active' : ''} onClick={() => setMode('reason')} aria-pressed={mode === 'reason'}>Deep reason</button>
            </div>
          </div>
          <div className="composer-input-row">
            <input
              id="facilitator-query"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Clarify the decision, surface evidence, or frame the next move…"
              disabled={queryBusy || connection !== 'online'}
            />
            <button className="send-button" type="submit" aria-label="Send facilitator question" disabled={!query.trim() || queryBusy || connection !== 'online'}>
              {queryBusy ? <span className="button-spinner" /> : <ArrowUp size={18} />}
            </button>
          </div>
        </form>
      </section>
    </main>
  )
}
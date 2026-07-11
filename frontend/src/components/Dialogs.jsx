import { useEffect, useRef, useState } from 'react'
import {
  Archive,
  BookOpenText,
  Check,
  Cpu,
  Database,
  FileDown,
  FileJson,
  FileText,
  HardDrive,
  Mic2,
  Plus,
  ShieldCheck,
  Sparkles,
  Upload,
  Volume2,
  X,
} from 'lucide-react'

function Dialog({ title, eyebrow, description, icon: Icon, onClose, children, size = 'medium' }) {
  const closeRef = useRef(null)

  useEffect(() => {
    const handleKey = (event) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKey)
    closeRef.current?.focus()
    return () => document.removeEventListener('keydown', handleKey)
  }, [onClose])

  return (
    <div className="dialog-layer" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className={`dialog dialog-${size}`} role="dialog" aria-modal="true" aria-labelledby="dialog-title">
        <header className="dialog-header">
          <div className="dialog-title-icon"><Icon size={20} /></div>
          <div>
            <span className="eyebrow">{eyebrow}</span>
            <h2 id="dialog-title">{title}</h2>
            {description && <p>{description}</p>}
          </div>
          <button ref={closeRef} className="icon-button dialog-close" type="button" aria-label="Close dialog" onClick={onClose}>
            <X size={18} />
          </button>
        </header>
        <div className="dialog-content">{children}</div>
      </section>
    </div>
  )
}

export function NewSessionDialog({ onClose, onCreate, busy }) {
  const [topic, setTopic] = useState('')

  const submit = async (event) => {
    event.preventDefault()
    await onCreate(topic.trim() || 'Untitled session')
  }

  return (
    <Dialog
      title="Open a new facilitation room"
      eyebrow="New session"
      description="Name the objective now, or leave it blank and ONF will title the room from the opening conversation."
      icon={Plus}
      onClose={onClose}
      size="small"
    >
      <form className="dialog-form" onSubmit={submit}>
        <label htmlFor="session-topic">Meeting objective or topic (optional)</label>
        <input
          id="session-topic"
          autoFocus
          value={topic}
          onChange={(event) => setTopic(event.target.value)}
          placeholder="Leave blank to title from the conversation"
          maxLength={120}
        />
        <div className="privacy-note"><ShieldCheck size={17} /><span><strong>Private by default.</strong> The transcript, knowledge and exports stay local.</span></div>
        <div className="dialog-actions">
          <button className="button button-ghost" type="button" onClick={onClose}>Cancel</button>
          <button className="button button-primary" type="submit" disabled={busy}>
            {busy ? 'Opening…' : 'Open workspace'}
          </button>
        </div>
      </form>
    </Dialog>
  )
}

export function VaultDialog({ capabilities, onClose, onAddNote, onUploadFile, busy }) {
  const [title, setTitle] = useState('')
  const [note, setNote] = useState('')

  const submit = async (event) => {
    event.preventDefault()
    if (!note.trim()) return
    await onAddNote({ title: title.trim() || 'Manual note', text: note.trim() })
    setTitle('')
    setNote('')
  }

  return (
    <Dialog
      title="Ground the meeting in local evidence"
      eyebrow="Knowledge vault"
      description="Add reference material for proactive recall and grounded facilitator answers. No cloud index is used."
      icon={Database}
      onClose={onClose}
      size="large"
    >
      <div className="vault-summary">
        <div><HardDrive size={19} /><span><strong>{capabilities.knowledge?.documents ?? 0}</strong> local chunks</span></div>
        <div><ShieldCheck size={19} /><span><strong>{capabilities.knowledge?.curated_chunks ?? 0}</strong> curated chunks</span></div>
        <div><BookOpenText size={19} /><span><strong>Source</strong> citations</span></div>
      </div>

      <div className="vault-grid">
        <form className="dialog-form vault-note-form" onSubmit={submit}>
          <div className="form-heading">
            <span className="step-number">01</span>
            <div><strong>Add a note</strong><small>Paste a policy, constraint, fact or agenda.</small></div>
          </div>
          <label htmlFor="knowledge-title">Source title</label>
          <input id="knowledge-title" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Security review notes" />
          <label htmlFor="knowledge-note">Local evidence</label>
          <textarea id="knowledge-note" value={note} onChange={(event) => setNote(event.target.value)} placeholder="Paste the evidence the facilitator should recall…" rows={7} />
          <button className="button button-primary align-self-start" type="submit" disabled={!note.trim() || busy}>
            <Plus size={16} /> Add to vault
          </button>
        </form>

        <div className="upload-zone-wrap">
          <div className="form-heading">
            <span className="step-number">02</span>
            <div><strong>Import a document</strong><small>PDF, Markdown or plain text up to 20 MB.</small></div>
          </div>
          <label className="upload-zone">
            <input type="file" accept=".pdf,.txt,.md" onChange={(event) => event.target.files[0] && onUploadFile(event.target.files[0])} disabled={busy} />
            <span className="upload-icon"><Upload size={22} /></span>
            <strong>Choose a local document</strong>
            <span>Content is chunked and embedded on-device.</span>
          </label>
        </div>
      </div>
    </Dialog>
  )
}

function CapabilityCard({ icon: Icon, title, value, detail, ready }) {
  return (
    <article className="system-card">
      <div className="system-card-icon"><Icon size={18} /></div>
      <div>
        <span>{title}</span>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
      <span className={`system-state${ready ? ' is-ready' : ''}`}>{ready ? <Check size={13} /> : null}{ready ? 'Ready' : 'Standby'}</span>
    </article>
  )
}

export function SystemDialog({ capabilities, skills, onUploadSkill, onClose, busy }) {
  const foundryReady = capabilities.foundry?.status === 'ready'
  return (
    <Dialog
      title="Know exactly what is running"
      eyebrow="Local capabilities"
      description="ONF keeps the workspace available while heavyweight models warm independently. Standby capabilities load only when used."
      icon={Cpu}
      onClose={onClose}
      size="large"
    >
      <div className="system-grid">
        <CapabilityCard icon={Cpu} title="Foundry Local" value={foundryReady ? 'Connected' : 'Not running'} detail={foundryReady ? `${capabilities.foundry.models?.length || 0} models visible` : 'Start the local service for model answers'} ready={foundryReady} />
        <CapabilityCard icon={Mic2} title="Transcription" value={capabilities.transcription?.model || 'Whisper'} detail="Loads on first microphone segment" ready={capabilities.transcription?.status === 'ready'} />
        <CapabilityCard icon={Database} title="Knowledge" value={`${capabilities.knowledge?.documents ?? 0} chunks`} detail={capabilities.knowledge?.embedding || 'Network-free local index'} ready={capabilities.knowledge?.status === 'ready'} />
        <CapabilityCard icon={Volume2} title="Local speech" value={capabilities.speech?.checkpoints_present ? 'Installed' : 'Optional'} detail="Loads only when an insight is played" ready={capabilities.speech?.status === 'ready'} />
      </div>

      <section className="skills-section">
        <div className="section-heading">
          <div><span className="eyebrow">Specialist layer</span><h3>Installed facilitator skills</h3></div>
          <label className="button button-secondary compact file-button">
            <Upload size={15} /> Install skill
            <input type="file" accept=".md" disabled={busy} onChange={(event) => event.target.files[0] && onUploadSkill(event.target.files[0])} />
          </label>
        </div>
        <div className="skills-list">
          {skills.length ? skills.map((skill) => (
            <div key={skill}><span><Sparkles size={14} /></span><strong>{skill}</strong><small>Trigger-aware</small></div>
          )) : <p>No skills have been installed.</p>}
        </div>
      </section>
    </Dialog>
  )
}

const EXPORTS = [
  { id: 'save', icon: Archive, title: 'Save session', text: 'Persist the full working state to a local JSON session file.', action: 'Save now' },
  { id: 'pdf', icon: FileDown, title: 'Executive brief', text: 'Generate a polished PDF with the summary, insights and transcript.', action: 'Create PDF' },
  { id: 'json', icon: FileJson, title: 'Portable archive', text: 'Export structured transcript, decisions, actions, risks and metrics.', action: 'Export JSON' },
  { id: 'markdown', icon: FileText, title: 'Meeting report', text: 'Create an editable Markdown record in FacilitatorReports.', action: 'Create report' },
]

export function ExportDialog({ onClose, onExport, busy }) {
  return (
    <Dialog
      title="Take the outcomes with you"
      eyebrow="Local export"
      description="Every format is generated on this machine and saved to your local FacilitatorReports folder."
      icon={FileDown}
      onClose={onClose}
      size="medium"
    >
      <div className="export-list">
        {EXPORTS.map(({ id, icon: Icon, title, text, action }) => (
          <article key={id} className="export-option">
            <span className="export-option-icon"><Icon size={19} /></span>
            <div><strong>{title}</strong><p>{text}</p></div>
            <button className="button button-secondary compact" type="button" disabled={busy} onClick={() => onExport(id)}>{action}</button>
          </article>
        ))}
      </div>
    </Dialog>
  )
}

export function Toast({ toast, onDismiss }) {
  if (!toast) return null
  return (
    <div className={`toast toast-${toast.type || 'info'}`} role={toast.type === 'error' ? 'alert' : 'status'}>
      <span>{toast.type === 'success' ? <Check size={17} /> : <Sparkles size={17} />}</span>
      <div><strong>{toast.title}</strong>{toast.message && <p>{toast.message}</p>}</div>
      <button className="quiet-icon-button" type="button" aria-label="Dismiss notification" onClick={onDismiss}><X size={16} /></button>
    </div>
  )
}
import { useCallback, useEffect, useState } from 'react'
import { AppHeader, Sidebar } from './components/AppChrome'
import {
  ExportDialog,
  NewSessionDialog,
  SystemDialog,
  Toast,
  VaultDialog,
} from './components/Dialogs'
import { IntelligencePanel } from './components/IntelligencePanel'
import { TranscriptWorkspace } from './components/TranscriptWorkspace'
import { useFacilitator } from './hooks/useFacilitator'
import { useSegmentRecorder } from './hooks/useSegmentRecorder'
import { audioUrl } from './lib/api'

function App() {
  const facilitator = useFacilitator()
  const [theme, setTheme] = useState(() => document.documentElement.getAttribute('data-theme') || 'light')
  const [mobileNavigation, setMobileNavigation] = useState(false)
  const [activeIntelligenceTab, setActiveIntelligenceTab] = useState('guidance')
  const [dialog, setDialog] = useState(null)
  const [skills, setSkills] = useState([])
  const [busyAction, setBusyAction] = useState('')
  const [queryBusy, setQueryBusy] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [actionToast, setActionToast] = useState(null)

  useEffect(() => {
    const topic = facilitator.state.session.topic
    document.title = topic && topic !== 'Untitled session' ? `${topic} — ONF` : 'ONF — Offline Neural Facilitator'
  }, [facilitator.state.session.topic])

  const showSuccess = useCallback((title, message = '') => {
    setActionToast({ type: 'success', title, message })
  }, [])

  const handleRecorderError = useCallback((error) => {
    setActionToast({ type: 'error', title: 'Microphone unavailable', message: error.message })
  }, [])

  const handleAudioSegment = useCallback(async (blob) => {
    const sent = await facilitator.sendAudio(blob)
    if (!sent) throw new Error('The local event stream is reconnecting. This segment was not sent.')
  }, [facilitator])

  const recorder = useSegmentRecorder(handleAudioSegment, handleRecorderError)

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark'
    document.documentElement.setAttribute('data-theme', next)
    setTheme(next)
  }

  const runDemo = async () => {
    setMobileNavigation(false)
    setActiveIntelligenceTab('guidance')
    setBusyAction('demo')
    try {
      await facilitator.run('/demo/start', { method: 'POST' })
      showSuccess('Showcase started', 'Watch the meeting move from tension to a controlled decision and owned next steps.')
    } finally {
      setBusyAction('')
    }
  }

  const askFacilitator = async (query, mode) => {
    setQueryBusy(true)
    try {
      await facilitator.run('/chat', {
        method: 'POST',
        body: JSON.stringify({ query, mode }),
      })
      await facilitator.refresh()
    } finally {
      setQueryBusy(false)
    }
  }

  const createSession = async (topic) => {
    setBusyAction('session')
    try {
      if (recorder.isRecording) recorder.stop()
      await facilitator.run('/session/new', {
        method: 'POST',
        body: JSON.stringify({ topic }),
      })
      await facilitator.refresh()
      setDialog(null)
      setActiveIntelligenceTab('guidance')
      showSuccess('Private workspace opened', topic)
    } finally {
      setBusyAction('')
    }
  }

  const addKnowledge = async (payload) => {
    setBusyAction('vault')
    try {
      const response = await facilitator.run('/upload-knowledge', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      await facilitator.refresh()
      showSuccess('Knowledge indexed locally', response.message)
    } finally {
      setBusyAction('')
    }
  }

  const uploadKnowledge = async (file) => {
    setBusyAction('vault')
    const body = new FormData()
    body.append('file', file)
    try {
      const response = await facilitator.run('/upload-file', { method: 'POST', body })
      await facilitator.refresh()
      showSuccess('Document indexed locally', response.message)
    } finally {
      setBusyAction('')
    }
  }

  const openSystem = async () => {
    setMobileNavigation(false)
    setDialog('system')
    try {
      const response = await facilitator.run('/skills')
      setSkills(response.skills || [])
    } catch {
      setSkills([])
    }
  }

  const uploadSkill = async (file) => {
    setBusyAction('skill')
    const body = new FormData()
    body.append('file', file)
    try {
      const response = await facilitator.run('/skills/upload', { method: 'POST', body })
      setSkills(response.skills || [])
      await facilitator.refresh()
      showSuccess('Facilitator skill installed', response.skill)
    } finally {
      setBusyAction('')
    }
  }

  const speakInsight = async (text) => {
    setSpeaking(true)
    try {
      const response = await facilitator.run('/tts/speak', {
        method: 'POST',
        body: JSON.stringify({ text, voice: 'EN-BR' }),
      })
      const audio = new Audio(audioUrl(response.audio_url))
      await audio.play()
    } finally {
      setSpeaking(false)
    }
  }

  const exportSession = async (kind) => {
    setBusyAction(`export-${kind}`)
    try {
      let response
      if (kind === 'save') {
        response = await facilitator.run('/session/save', { method: 'POST' })
      } else if (kind === 'json') {
        response = await facilitator.run('/export/json', { method: 'POST' })
      } else {
        const summary = await facilitator.run('/summary', { method: 'POST' })
        const payload = JSON.stringify({
          transcript: facilitator.state.transcript,
          insights: facilitator.state.insights,
          summary: summary.summary,
          topic: facilitator.state.session.topic,
        })
        response = await facilitator.run(kind === 'pdf' ? '/report/export/pdf' : '/report/generate', {
          method: 'POST',
          body: payload,
        })
      }
      showSuccess('Local export complete', response.filepath)
      setDialog(null)
    } finally {
      setBusyAction('')
    }
  }

  const openOutcomes = () => {
    setMobileNavigation(false)
    setActiveIntelligenceTab(facilitator.state.decisions.length ? 'decisions' : 'actions')
    window.requestAnimationFrame(() => document.getElementById('outcomes-panel')?.scrollIntoView({ behavior: 'smooth' }))
  }

  const visibleToast = actionToast || (facilitator.lastError
    ? { type: 'error', title: 'Local capability needs attention', message: facilitator.lastError }
    : null)

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to live workspace</a>
      <AppHeader
        connection={facilitator.connection}
        theme={theme}
        onToggleTheme={toggleTheme}
        onExport={() => setDialog('export')}
        onToggleNavigation={() => setMobileNavigation(true)}
      />
      <div className="app-body">
        <Sidebar
          capabilities={facilitator.capabilities}
          mobileOpen={mobileNavigation}
          onClose={() => setMobileNavigation(false)}
          onOpenVault={() => { setMobileNavigation(false); setDialog('vault') }}
          onOpenSystem={openSystem}
          onOpenOutcomes={openOutcomes}
          onRunDemo={runDemo}
          demoRunning={busyAction === 'demo' || facilitator.state.session.status === 'showcase'}
        />
        <div className="workspace-layout">
          <TranscriptWorkspace
            state={facilitator.state}
            connection={facilitator.connection}
            isRecording={recorder.isRecording}
            segmentsSent={recorder.segmentsSent}
            onToggleRecording={recorder.isRecording ? recorder.stop : recorder.start}
            onRunDemo={runDemo}
            onAsk={askFacilitator}
            onNewSession={() => setDialog('session')}
            queryBusy={queryBusy}
          />
          <IntelligencePanel
            state={facilitator.state}
            activeTab={activeIntelligenceTab}
            onTabChange={setActiveIntelligenceTab}
            onSpeak={speakInsight}
            speaking={speaking}
          />
        </div>
      </div>

      {dialog === 'session' && <NewSessionDialog onClose={() => setDialog(null)} onCreate={createSession} busy={busyAction === 'session'} />}
      {dialog === 'vault' && <VaultDialog capabilities={facilitator.capabilities} onClose={() => setDialog(null)} onAddNote={addKnowledge} onUploadFile={uploadKnowledge} busy={busyAction === 'vault'} />}
      {dialog === 'system' && <SystemDialog capabilities={facilitator.capabilities} skills={skills} onUploadSkill={uploadSkill} onClose={() => setDialog(null)} busy={busyAction === 'skill'} />}
      {dialog === 'export' && <ExportDialog onClose={() => setDialog(null)} onExport={exportSession} busy={busyAction.startsWith('export-')} />}

      <Toast
        toast={visibleToast}
        onDismiss={() => {
          setActionToast(null)
          facilitator.clearError()
        }}
      />
    </div>
  )
}

export default App
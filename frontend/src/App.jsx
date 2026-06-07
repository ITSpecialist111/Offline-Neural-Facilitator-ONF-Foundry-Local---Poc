import { useState, useRef, useEffect, useMemo } from 'react'
import { Mic, Square, Play, Activity, List, AlertTriangle, MessageSquare, Power, Zap, ChevronRight, BarChart3, Clock, Settings, Brain } from 'lucide-react'
import ChatWidget from './components/ChatWidget'
import AnalyticsDashboard from './components/AnalyticsDashboard'
import VADIndicator from './components/VADIndicator'
import { apiUrl, wsUrl } from './config'
import { speak } from './speech'
import './DesignSystem.css'

const TranscriptItem = ({ msg, isActive }) => {
  if (msg.role === 'system' && msg.isEvent) {
    return (
      <div className="flex gap-4 flex-row-reverse mb-8 group">
        <div className="w-8 h-8 rounded-full bg-accent-gold text-black flex items-center justify-center shrink-0 gold-glow">
          <Zap size={14} fill="currentColor" />
        </div>
        <div className="max-w-xl">
          <div className="p-4 rounded-2xl bg-gradient-to-br from-amber-400 to-amber-600 text-black font-semibold shadow-lg">
            {msg.text}
            {msg.citation && (
              <div className="mt-2 pt-2 border-t border-black/10 text-[10px] uppercase tracking-widest font-bold">
                Ref: {msg.citation}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`mb-6 transition-opacity duration-500 ${isActive ? 'opacity-100' : 'opacity-40'}`}>
      <p className={`spotify-lyrics-text ${isActive ? 'active' : ''}`}>
        {msg.text}
      </p>
    </div>
  );
};

function App() {
  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState([])
  const [insights, setInsights] = useState([])
  const [status, setStatus] = useState("Ready")
  const [isDeepThink, setIsDeepThink] = useState(false)
  const [activeTab, setActiveTab] = useState('live')
  const [skills, setSkills] = useState([])
  const [showAnalytics, setShowAnalytics] = useState(false)
  const [vadEnergy, setVadEnergy] = useState(0)
  // Stable per-session id (computed once, not on every render).
  const [sessionId] = useState(() => {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID().split('-')[0].toUpperCase()
    }
    // Fallback for older browsers (non-security use: display/correlation only).
    const bytes = new Uint8Array(8)
    if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
      crypto.getRandomValues(bytes)
    }
    return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('').toUpperCase()
  })
  const mediaRecorderRef = useRef(null)
  const socketRef = useRef(null)
  const fileInputRef = useRef(null)
  const transcriptEndRef = useRef(null)

  // Auto-scroll transcript
  useEffect(() => {
    if (transcriptEndRef.current) {
      transcriptEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [transcript])

  useEffect(() => {
    fetch(apiUrl('/skills'))
      .then(res => res.json())
      .then(data => setSkills(data.skills))
      .catch(err => console.error("Failed to load skills", err))
  }, [])

  const handleSkillUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(apiUrl('/skills/upload'), {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (data.status === 'success') {
        setSkills(prev => [...prev, data.skill])
        setInsights(prev => [{ type: 'System', text: `Skill '${data.skill}' installed` }, ...prev])
      }
    } catch (err) {
      console.error("Upload failed", err)
      setInsights(prev => [{ type: 'System', text: 'Skill upload failed' }, ...prev])
    }
  }

  // Load state from localStorage on mount
  useEffect(() => {
    const savedTranscript = localStorage.getItem('onf_transcript')
    if (savedTranscript) setTranscript(JSON.parse(savedTranscript))

    const savedInsights = localStorage.getItem('onf_insights')
    if (savedInsights) setInsights(JSON.parse(savedInsights))
  }, [])

  // Save state to localStorage on change
  useEffect(() => {
    localStorage.setItem('onf_transcript', JSON.stringify(transcript))
  }, [transcript])

  useEffect(() => {
    localStorage.setItem('onf_insights', JSON.stringify(insights))
  }, [insights])

  const generateReport = async (summaryText) => {
    try {
      const agenda = insights.find(i => i.type === 'Agenda')?.text || "General"
      const res = await fetch(apiUrl("/report/generate"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          transcript: transcript,
          insights: insights,
          summary: summaryText,
          topic: agenda
        })
      })
      const data = await res.json()
      if (data.status === "success") {
        setInsights(prev => [{ type: 'System', text: `Report saved to ${data.filepath}` }, ...prev])
      }
    } catch (e) { console.error(e) }
  }

  useEffect(() => {
    // Connect WebSocket on mount
    const socket = new WebSocket(wsUrl("/ws/stream"))
    socket.onopen = () => {
      console.log("WebSocket connected")
      // setStatus("Ready") // Don't override status here if it's "Ready" default
    }

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'transcript') {
        setTranscript(prev => [...prev, {
          role: 'user',
          text: data.text,
          segments: data.segments
        }])
      } else if (data.type === 'timeline_event') {
        setTranscript(prev => [...prev, {
          role: 'system',
          isEvent: true,
          subtype: data.subtype,
          text: data.text,
          citation: data.citation
        }])
        // Also push to Insights list for sidebar
        setInsights(prev => [data, ...prev])
      } else if (data.type === 'voice_activity') {
        setVadEnergy(data.energy)
      }
    }

    socketRef.current = socket

    return () => {
      socket.close()
    }
  }, [])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      mediaRecorderRef.current = mediaRecorder

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
          socketRef.current.send(event.data)
        }
      }

      mediaRecorder.start(1000)
      setIsRecording(true)
      setStatus("Listening...")
    } catch (err) {
      console.error("Error accessing microphone:", err)
      setStatus(`Error: ${err.message}`)
    }
  }

  const stopRecording = async () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      setStatus("Processing session...")

      // Save Session
      try {
        const res = await fetch(apiUrl('/session/save'), { method: 'POST' })
        if (res.ok) {
          console.log("Session saved")
          setStatus("Session Ended")
          setShowAnalytics(true)
        }
      } catch (e) {
        console.error("Error saving session:", e)
      }
    }
  }

  const captureScreen = async () => {
    try {
      const res = await fetch(apiUrl('/vision/capture'), { method: 'POST' })
      const data = await res.json()
      if (data.status === 'success') {
        setInsights(prev => [{ type: 'System', text: `Snapshot captured: ${data.filepath.split('\\').pop()}` }, ...prev])
      }
    } catch (error) {
      console.error("Capture failed:", error)
      setInsights(prev => [{ type: 'System', text: 'Snapshot failed' }, ...prev])
    }
  }

  const handleTTS = async (text) => {
    // Uses backend TTS when available, otherwise the browser's offline Web Speech API.
    await speak(text)
  }

  return (
    <div className="h-screen bg-black text-white flex flex-col overflow-hidden selection:bg-amber-500/30">

      {/* Main Container */}
      <div className="flex-1 flex overflow-hidden">

        {/* Left Sidebar - Navigation & Library */}
        <div className="w-64 bg-black flex flex-col border-r border-white/5 hidden md:flex">
          <div className="p-6 flex flex-col h-full">
            <div className="mb-8">
              <h1 className="text-xl font-black tracking-tighter flex items-center gap-2 mb-6">
                <div className="w-8 h-8 bg-accent-gold rounded-full flex items-center justify-center text-black">
                  <Zap size={18} fill="currentColor" />
                </div>
                ONF <span className="text-accent-gold">GOLD</span>
              </h1>

              <nav className="space-y-2 mt-2">
                <div className="sidebar-item active">
                  <Activity size={18} />
                  <span>Live Session</span>
                </div>
                <div className="sidebar-item" onClick={() => setShowAnalytics(true)}>
                  <BarChart3 size={18} />
                  <span>Analytics</span>
                </div>
                <div className="sidebar-item opacity-50 cursor-not-allowed" title="Coming Soon">
                  <Clock size={18} />
                  <span>History</span>
                </div>
                <div className="sidebar-item opacity-50 cursor-not-allowed" title="Coming Soon">
                  <Settings size={18} />
                  <span>Settings</span>
                </div>
              </nav>
            </div>

            {/* Skills & Vault */}
            <div className="flex-1 overflow-y-auto no-scrollbar space-y-6">
              <div>
                <div className="flex items-center justify-between px-4 mb-2">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted">Skills</span>
                  <button onClick={() => fileInputRef.current.click()} className="text-text-muted hover:text-white transition-colors">
                    <Zap size={12} />
                  </button>
                  <input type="file" ref={fileInputRef} className="hidden" accept=".md" onChange={handleSkillUpload} />
                </div>
                <div className="space-y-1 px-2">
                  {skills.map((skill, i) => (
                    <div key={i} className="text-xs py-2 px-3 rounded-md hover:bg-white/5 text-text-secondary flex items-center gap-2">
                      <div className="w-1 h-1 rounded-full bg-accent-emerald"></div>
                      {skill}
                    </div>
                  ))}
                  {skills.length === 0 && <p className="text-[10px] text-text-muted italic px-3">No custom skills</p>}
                </div>
              </div>

              <div>
                <div className="px-4 mb-4">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted">Knowledge Vault</span>
                </div>
                <div className="px-4">
                  <div className="p-3 rounded-xl bg-bg-surface border border-white/5 focus-within:border-accent-gold/50 transition-all">
                    <textarea
                      placeholder="Feed memory..."
                      className="w-full bg-transparent border-none text-xs text-text-primary focus:outline-none resize-none h-20"
                      onKeyDown={async (e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          if (!e.target.value.trim()) return;
                          try {
                            await fetch(apiUrl("/upload-knowledge"), {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({ text: e.target.value })
                            });
                            setInsights(prev => [{ type: 'System', text: 'Memory updated' }, ...prev]);
                            e.target.value = "";
                          } catch (err) { console.error(err); }
                        }
                      }}
                    />
                    <div className="flex justify-between items-center mt-2 pt-2 border-t border-white/5">
                      <span className="text-[9px] text-text-muted">Enter to save</span>
                      <label className="cursor-pointer text-accent-gold hover:text-white transition-colors">
                        <input type="file" className="hidden" accept=".pdf,.txt" onChange={async (e) => {
                          const file = e.target.files[0];
                          if (!file) return;
                          setInsights(prev => [{ type: 'System', text: `Syncing ${file.name}...` }, ...prev]);
                          const formData = new FormData();
                          formData.append("file", file);
                          try {
                            const res = await fetch(apiUrl("/upload-file"), { method: "POST", body: formData });
                            if (res.ok) setInsights(prev => [{ type: 'System', text: 'Vault updated' }, ...prev]);
                          } catch (err) { console.error(err); }
                        }} />
                        <MessageSquare size={12} />
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Center Stage - Real-Time Transcript */}
        <div className="flex-1 bg-gradient-to-b from-bg-surface to-bg-base overflow-y-auto no-scrollbar relative flex flex-col items-center">

          {/* Stage Header */}
          <div className="max-w-4xl w-full px-8 pt-12 pb-8 sticky top-0 z-20 bg-gradient-to-b from-bg-surface to-transparent">
            <div className="flex items-end justify-between">
              <div>
                <h2 className="text-4xl font-extrabold tracking-tight text-white mb-2">
                  {activeTab === 'live' ? 'Live Facilitation' : activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
                </h2>
                <div className="flex items-center gap-3">
                  <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-widest ${isRecording ? 'bg-red-500/10 text-red-500 animate-pulse' : 'bg-accent-emerald/10 text-accent-emerald'}`}>
                    <div className={`w-1.5 h-1.5 rounded-full ${isRecording ? 'bg-red-500' : 'bg-accent-emerald'}`}></div>
                    {status}
                  </div>
                  <span className="text-text-muted text-xs">• Session ID: {sessionId}</span>
                </div>
              </div>

              {/* Visual VAD */}
              <VADIndicator energy={vadEnergy} isRecording={isRecording} />
            </div>
          </div>

          <div className="max-w-4xl w-full px-8 pb-48 pt-12 space-y-2">
            {transcript.length === 0 && !isRecording && (
              <div className="h-64 flex flex-col items-center justify-center text-text-muted space-y-4">
                <div className="w-16 h-16 rounded-full bg-bg-elevated flex items-center justify-center">
                  <Mic size={32} />
                </div>
                <p className="font-medium">Waiting to capture the conversation...</p>
              </div>
            )}

            {transcript.map((msg, idx) => (
              <TranscriptItem key={idx} msg={msg} isActive={idx === transcript.length - 1} />
            ))}
            <div ref={transcriptEndRef} />
          </div>
        </div>

        {/* Right Panel - Proactive Insights (Now Playing) */}
        <div className="w-96 bg-black border-l border-white/5 hidden lg:flex flex-col">
          <div className="p-6 space-y-6 flex-1 overflow-y-auto no-scrollbar">

            {/* Tab Switcher */}
            <div className="p-1 rounded-xl bg-bg-surface flex">
              {[
                { id: 'live', label: 'Live', icon: Activity },
                { id: 'actions', label: 'Actions', icon: Zap },
                { id: 'risks', label: 'Risks', icon: AlertTriangle }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex-1 py-3 flex flex-col items-center justify-center gap-1 text-[9px] font-bold uppercase tracking-widest rounded-lg transition-all ${activeTab === tab.id ? 'bg-accent-gold text-black gold-glow' : 'text-text-secondary hover:text-white hover:bg-white/5'}`}
                >
                  <tab.icon size={16} fill={activeTab === tab.id ? "currentColor" : "none"} />
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Dynamic Insights Feed */}
            <div className="space-y-4">
              <div className="flex items-center justify-between px-2">
                <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted">
                  {activeTab === 'live' ? 'Now Playing' : `Detected ${activeTab}`}
                </span>
                <Activity size={12} className="text-accent-gold" />
              </div>

              {activeTab === 'live' && insights.map((insight, i) => (
                <div key={i} className="premium-card p-4 group">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2">
                      <div className={`w-6 h-6 rounded-md flex items-center justify-center ${insight.type === 'Proactive' ? 'bg-accent-gold/10 text-accent-gold' : 'bg-white/5 text-text-muted'}`}>
                        {insight.type === 'Proactive' ? <Zap size={12} fill="currentColor" /> : <Activity size={12} />}
                      </div>
                      <span className="text-[10px] font-bold uppercase tracking-widest text-text-secondary">{insight.type}</span>
                    </div>
                    <button onClick={() => handleTTS(insight.text)} className="opacity-0 group-hover:opacity-100 transition-opacity text-text-muted hover:text-white">
                      <Play size={12} fill="currentColor" />
                    </button>
                  </div>
                  <p className="text-sm leading-relaxed text-text-primary">{insight.text}</p>
                  {insight.citation && (
                    <div className="mt-3 text-[10px] font-mono text-accent-gold/60 flex items-center gap-2">
                      <ChevronRight size={10} /> {insight.citation}
                    </div>
                  )}
                </div>
              ))}

              {activeTab === 'actions' && (
                <div className="space-y-4">
                  <button
                    onClick={async () => {
                      const res = await fetch(apiUrl("/action-items"), { method: "POST" });
                      const data = await res.json();
                      if (data.action_items) setInsights(prev => [{ type: 'Proactive', text: `Action Item: ${data.action_items}` }, ...prev]);
                    }}
                    className="w-full py-4 rounded-xl border border-dashed border-white/10 text-[10px] font-bold uppercase tracking-widest text-text-muted hover:border-accent-gold hover:text-white transition-all"
                  >
                    Detect Action Items
                  </button>
                  {insights.filter(i => i.text.toLowerCase().includes('action') || i.type === 'Proactive').map((insight, i) => (
                    <div key={i} className="premium-card p-4">
                      <p className="text-sm text-text-primary">{insight.text}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Control Bar - "The Player" */}
      <div className="h-24 bg-bg-base border-t border-white/5 px-8 flex items-center justify-between z-30">

        {/* Playback Info */}
        <div className="w-1/4 flex items-center gap-4">
          <div className={`w-14 h-14 rounded-lg bg-bg-surface flex items-center justify-center transition-all ${isRecording ? 'gold-glow' : ''}`}>
            <Brain size={28} className={isRecording ? 'text-accent-gold' : 'text-text-muted'} />
          </div>
          <div>
            <p className="text-sm font-bold truncate max-w-[200px]">{isRecording ? "Live Facilitation Active" : "Session Paused"}</p>
            <p className="text-xs text-text-muted">On-Device Intelligence</p>
          </div>
        </div>

        {/* Player Controls */}
        <div className="w-1/2 flex flex-col items-center gap-3">
          <div className="flex items-center gap-6">
            <button
              onClick={() => setIsDeepThink(!isDeepThink)}
              className={`control-btn ${isDeepThink ? 'text-accent-gold border-accent-gold' : 'text-text-muted'}`}
              title="Deep Reasoning (Toggle)"
            >
              <Zap size={20} fill={isDeepThink ? "currentColor" : "none"} />
            </button>

            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={`hero-btn rounded-full shadow-2xl flex items-center justify-center transition-all ${isRecording ? 'bg-red-500 text-white animate-pulse' : 'bg-white text-black hover:scale-105'}`}
            >
              {isRecording ? <Square size={24} fill="currentColor" /> : <Mic size={24} fill="currentColor" />}
            </button>

            <button onClick={captureScreen} className="control-btn text-text-muted hover:text-white" title="Screen Vision">
              <Square size={20} />
            </button>
          </div>

          {/* Progress Slider (Mock for aesthetic) */}
          <div className="w-full max-w-md flex items-center gap-3">
            <span className="text-[10px] text-text-muted font-mono">0:00</span>
            <div className="flex-1 h-1 bg-white/10 rounded-full group cursor-pointer relative overflow-hidden">
              <div className={`h-full bg-accent-gold transition-all duration-1000 ${isRecording ? 'w-full animate-pulse' : 'w-0'}`}></div>
            </div>
            <span className={`text-[10px] font-mono transition-colors ${isRecording ? 'text-red-500 font-bold animate-pulse' : 'text-text-muted'}`}>
              {isRecording ? 'REC' : 'LIVE'}
            </span>
          </div>
        </div>

        {/* Secondary Controls */}
        <div className="w-1/4 flex items-center justify-end gap-6">
          <button
            onClick={async () => {
              setStatus("Generating PDF...");
              try {
                const agenda = insights.find(i => i.type === 'Agenda')?.text || "General"
                const summary = insights.find(i => i.type === 'Summary')?.text || ""
                const res = await fetch(apiUrl("/report/export/pdf"), {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    transcript,
                    insights,
                    summary,
                    topic: agenda
                  })
                });
                const data = await res.json();
                if (data.status === "success") {
                  setInsights(prev => [{ type: 'System', text: `PDF Report saved to ${data.filepath}` }, ...prev]);
                }
                setStatus("Ready");
              } catch (e) {
                console.error(e);
                setStatus("Error generating PDF");
              }
            }}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-neutral-600 text-xs font-bold text-neutral-300 hover:border-white hover:text-white transition-colors"
          >
            <Power size={14} className="text-red-400" /> EXPORT PDF
          </button>
          <button
            onClick={async () => {
              setStatus("Summarizing...");
              try {
                const res = await fetch(apiUrl("/summary"), { method: "POST" });
                const data = await res.json();
                setInsights(prev => [{ type: 'Summary', text: data.summary }, ...prev]);
                setStatus("Ready");
              } catch (e) { console.error(e); }
            }}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-neutral-600 text-xs font-bold text-neutral-300 hover:border-white hover:text-white transition-colors"
          >
            <List size={14} /> GENERATE SUMMARY
          </button>
          <button className="text-text-muted hover:text-white transition-colors" onClick={() => setShowAnalytics(true)}>
            <BarChart3 size={20} />
          </button>
        </div>
      </div>

      <ChatWidget />
      <AnalyticsDashboard
        isOpen={showAnalytics}
        onClose={() => setShowAnalytics(false)}
        transcript={transcript}
        actionItems={insights
          .filter(i => (i.type === 'Proactive' || i.type === 'System') && i.text.toLowerCase().includes('action'))
          .map(i => i.text)}
      />
    </div>
  )

}

export default App

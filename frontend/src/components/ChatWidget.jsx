import { useState, useRef, useEffect } from 'react'
import { MessageSquare, X, Send, Bot, User } from 'lucide-react'

export default function ChatWidget() {
    const [isOpen, setIsOpen] = useState(false)
    const [messages, setMessages] = useState([
        { role: 'assistant', text: 'Facilitator ready. How can I assist with the session or intelligence vault?' }
    ])
    const [input, setInput] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const messagesEndRef = useRef(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages, isOpen])

    const handleSend = async () => {
        if (!input.trim()) return

        const userMsg = { role: 'user', text: input }
        setMessages(prev => [...prev, userMsg])
        setInput('')
        setIsLoading(true)

        try {
            const res = await fetch("http://localhost:8000/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: userMsg.text })
            })
            const data = await res.json()
            setMessages(prev => [...prev, { role: 'assistant', text: data.response }])
        } catch (err) {
            setMessages(prev => [...prev, { role: 'assistant', text: "Neural link interrupted." }])
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="fixed bottom-32 right-8 z-50 flex flex-col items-end pointer-events-none">
            {/* Chat Window */}
            <div className={`mb-6 w-96 glass-panel rounded-3xl overflow-hidden transition-all duration-500 origin-bottom-right pointer-events-auto shadow-2xl ${isOpen ? 'translate-y-0 opacity-100 scale-100' : 'translate-y-12 opacity-0 scale-90 pointer-events-none h-0 opacity-0'}`}>
                {/* Header */}
                <div className="p-5 bg-white/5 border-b border-white/5 flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-accent-gold flex items-center justify-center text-black shadow-lg">
                            <Bot size={16} fill="currentColor" />
                        </div>
                        <div>
                            <span className="block text-[10px] font-black text-accent-gold uppercase tracking-[0.2em]">Neural Agent</span>
                            <span className="block text-xs font-bold text-white">Foundry Intelligence</span>
                        </div>
                    </div>
                    <button onClick={() => setIsOpen(false)} className="w-8 h-8 rounded-full hover:bg-white/10 flex items-center justify-center transition-colors text-text-muted hover:text-white">
                        <X size={16} />
                    </button>
                </div>

                {/* Messages */}
                <div className="h-[400px] overflow-y-auto p-6 space-y-4 no-scrollbar bg-black/40">
                    {messages.map((msg, i) => (
                        <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                            <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 shadow-sm ${msg.role === 'user' ? 'bg-white text-black' : 'bg-bg-elevated text-accent-gold border border-white/5'}`}>
                                {msg.role === 'user' ? <User size={14} fill="currentColor" /> : <Bot size={14} fill="currentColor" />}
                            </div>
                            <div className={`p-4 rounded-2xl text-xs leading-relaxed max-w-[80%] shadow-sm ${msg.role === 'user'
                                ? 'bg-white text-black font-medium rounded-tr-none'
                                : 'bg-bg-elevated text-text-primary border border-white/5 rounded-tl-none'
                                }`}>
                                {msg.text}
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex gap-3">
                            <div className="w-8 h-8 rounded-xl bg-bg-elevated text-accent-gold border border-white/5 flex items-center justify-center shrink-0"><Bot size={14} fill="currentColor" /></div>
                            <div className="flex items-center gap-1.5 p-4 rounded-2xl bg-bg-elevated border border-white/5">
                                <span className="w-1 h-1 bg-accent-gold rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                                <span className="w-1 h-1 bg-accent-gold rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                                <span className="w-1 h-1 bg-accent-gold rounded-full animate-bounce"></span>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className="p-5 bg-white/5 border-t border-white/5">
                    <div className="flex items-center gap-3 bg-black/40 border border-white/10 rounded-2xl p-2 pl-4 focus-within:border-accent-gold/40 transition-all">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                            placeholder="Type a neural query..."
                            className="flex-1 bg-transparent text-xs text-white placeholder:text-text-muted focus:outline-none"
                        />
                        <button
                            onClick={handleSend}
                            disabled={isLoading || !input.trim()}
                            className="w-10 h-10 bg-accent-gold text-black rounded-xl flex items-center justify-center shadow-lg hover:scale-105 active:scale-95 disabled:opacity-30 disabled:hover:scale-100 transition-all"
                        >
                            <Send size={16} fill="currentColor" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Toggle Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`w-16 h-16 rounded-full shadow-2xl flex items-center justify-center transition-all duration-500 pointer-events-auto gold-glow border-2 border-white/10 ${isOpen ? 'bg-bg-elevated text-white rotate-90 scale-110' : 'bg-accent-gold text-black hover:scale-110 active:scale-95'}`}
            >
                {isOpen ? <X size={24} /> : <MessageSquare size={24} fill="currentColor" />}
            </button>
        </div>
    )
}

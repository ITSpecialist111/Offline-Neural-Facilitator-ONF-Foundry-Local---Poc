import React from 'react'
import { PieChart, Clock, CheckSquare, BarChart2, List, Activity, AlertTriangle } from 'lucide-react'

const AnalyticsDashboard = ({ transcript = [], actionItems = [], isOpen, onClose }) => {
    if (!isOpen) return null

    // Calculate Metrics
    const totalMessages = transcript?.length || 0
    const userMessages = transcript?.filter(m => m.role === 'user').length || 0
    const systemMessages = transcript?.filter(m => m.role === 'assistant' || m.role === 'system').length || 0

    const userRatio = totalMessages > 0 ? Math.round((userMessages / totalMessages) * 100) : 0
    const systemRatio = totalMessages > 0 ? Math.round((systemMessages / totalMessages) * 100) : 0

    const deviation = Math.abs(userRatio - 70)
    const healthScore = Math.max(0, 100 - (deviation * 2))

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xl z-[60] flex items-center justify-center p-8 animate-in fade-in zoom-in duration-300">
            <div className="bg-bg-elevated border border-white/5 rounded-3xl p-10 max-w-5xl w-full max-h-[85vh] overflow-hidden shadow-2xl flex flex-col">

                <div className="flex items-center justify-between mb-10">
                    <div>
                        <h2 className="text-4xl font-black tracking-tighter text-white">
                            Session <span className="text-accent-gold">Analytics</span>
                        </h2>
                        <p className="text-text-muted text-sm font-medium mt-1">Foundry Local • Real-time Intelligence</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="px-6 py-2.5 rounded-full bg-white/5 hover:bg-white/10 text-white text-xs font-bold uppercase tracking-widest transition-all border border-white/5"
                    >
                        Close Report
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto no-scrollbar space-y-10">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {/* Health Score Card */}
                        <div className="premium-card p-8 flex flex-col justify-between h-48 relative overflow-hidden">
                            <div className="absolute -right-6 -top-6 w-24 h-24 bg-accent-gold/5 rounded-full blur-2xl"></div>
                            <div className="flex items-center gap-3 text-text-muted">
                                <BarChart2 size={24} className="gold-glow" />
                                <h3 className="font-bold uppercase tracking-widest text-[10px]">Session Health</h3>
                            </div>
                            <div>
                                <div className="text-5xl font-black text-white mb-2">{healthScore}</div>
                                <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                                    <div className="h-full bg-accent-gold rounded-full" style={{ width: `${healthScore}%` }}></div>
                                </div>
                            </div>
                        </div>

                        {/* Talk Time Card */}
                        <div className="premium-card p-8 flex flex-col justify-between h-48">
                            <div className="flex items-center gap-3 text-text-muted">
                                <Clock size={24} className="gold-glow" />
                                <h3 className="font-bold uppercase tracking-widest text-[10px]">Talk Balance</h3>
                            </div>
                            <div className="space-y-4">
                                <div className="flex items-end justify-between">
                                    <div>
                                        <div className="text-3xl font-black text-white">{userRatio}%</div>
                                        <p className="text-[10px] uppercase font-bold text-text-muted tracking-widest">Speaker</p>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-3xl font-black text-accent-gold">{systemRatio}%</div>
                                        <p className="text-[10px] uppercase font-bold text-text-muted tracking-widest">Facilitator</p>
                                    </div>
                                </div>
                                <div className="flex h-1.5 rounded-full overflow-hidden bg-white/5">
                                    <div className="bg-white" style={{ width: `${userRatio}%` }}></div>
                                    <div className="bg-accent-gold" style={{ width: `${systemRatio}%` }}></div>
                                </div>
                            </div>
                        </div>

                        {/* Actions Card */}
                        <div className="premium-card p-8 flex flex-col justify-between h-48">
                            <div className="flex items-center gap-3 text-text-muted">
                                <CheckSquare size={24} className="gold-glow" />
                                <h3 className="font-bold uppercase tracking-widest text-[10px]">Neural Triggers</h3>
                            </div>
                            <div>
                                <div className="text-5xl font-black text-accent-emerald mb-1">{actionItems.length}</div>
                                <p className="text-[10px] uppercase font-bold text-text-muted tracking-widest">Actionable Insights</p>
                            </div>
                        </div>
                    </div>

                    {/* Action Item List */}
                    <div className="premium-card p-10 overflow-hidden relative">
                        <div className="flex items-center justify-between mb-8">
                            <h3 className="font-black text-xl flex items-center gap-3">
                                <Zap size={20} className="text-accent-gold" fill="currentColor" />
                                Detected Action Items
                            </h3>
                            <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest bg-white/5 px-3 py-1 rounded-md border border-white/5">Auto-generated</span>
                        </div>

                        {actionItems.length === 0 ? (
                            <div className="h-40 flex flex-col items-center justify-center text-text-muted italic space-y-3">
                                <List size={24} className="opacity-20" />
                                <p className="text-sm">No action items detected by the facilitator yet.</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {actionItems.map((item, i) => (
                                    <div key={i} className="flex items-center gap-4 p-5 bg-bg-surface rounded-2xl border border-white/5 hover:border-accent-gold/30 transition-all group">
                                        <div className="w-5 h-5 rounded-full border border-accent-gold/50 flex items-center justify-center shrink-0">
                                            <div className="w-2 h-2 bg-accent-gold rounded-full scale-0 group-hover:scale-100 transition-transform" />
                                        </div>
                                        <p className="text-sm text-text-secondary leading-relaxed group-hover:text-white transition-colors">{item}</p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default AnalyticsDashboard

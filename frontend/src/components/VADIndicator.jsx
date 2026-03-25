import React from 'react';
import { Activity } from 'lucide-react';

const VADIndicator = ({ energy = 0, isRecording = false }) => {
    // Normalize energy for CSS variables (0 to 1)
    const normalizedEnergy = energy / 100;

    return (
        <div className="flex items-center gap-4 px-4 py-2 rounded-2xl bg-bg-surface border border-white/5 backdrop-blur-xl">
            <div className="relative flex items-center justify-center">
                {/* Pulsing Aura */}
                <div
                    className="absolute w-8 h-8 rounded-full bg-accent-gold transition-all duration-75"
                    style={{
                        opacity: isRecording ? 0.1 + (normalizedEnergy * 0.4) : 0,
                        transform: `scale(${1 + (normalizedEnergy * 1.5)})`,
                        filter: 'blur(8px)'
                    }}
                />

                {/* Core Ring */}
                <div
                    className={`w-10 h-10 rounded-full border-2 flex items-center justify-center transition-all duration-100 ${isRecording ? 'border-accent-gold' : 'border-white/10'
                        }`}
                    style={{
                        boxShadow: isRecording ? `0 0 ${normalizedEnergy * 20}px var(--accent-gold)` : 'none'
                    }}
                >
                    <Activity
                        size={18}
                        className={`transition-colors ${isRecording ? 'text-accent-gold' : 'text-text-muted'}`}
                        style={{
                            transform: `scale(${1 + (normalizedEnergy * 0.2)})`
                        }}
                    />
                </div>
            </div>

            <div className="flex flex-col">
                <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-text-muted">
                    Signal Strength
                </span>
                <div className="flex gap-0.5 mt-1 h-1.5 w-24 bg-white/5 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-accent-gold transition-all duration-75"
                        style={{ width: `${energy}%` }}
                    />
                </div>
            </div>
        </div>
    );
};

export default VADIndicator;

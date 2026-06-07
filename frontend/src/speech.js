// Offline text-to-speech helper.
//
// Strategy:
//  1. Ask the backend to render speech (MeloTTS/OpenVoice) when that optional
//     capability is enabled. The backend returns 503 when it isn't.
//  2. On any failure, fall back to the browser's built-in, fully-offline
//     Web Speech API (window.speechSynthesis). This keeps the "Play" feature
//     working everywhere without the heavy native TTS stack.

import { apiUrl } from './config'

export function browserSpeak(text) {
  try {
    if (typeof window === 'undefined' || !('speechSynthesis' in window) || !text) {
      return false
    }
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.rate = 1.0
    utterance.pitch = 1.0
    window.speechSynthesis.speak(utterance)
    return true
  } catch (err) {
    console.error('Browser speech synthesis failed', err)
    return false
  }
}

export async function speak(text) {
  if (!text) return
  try {
    const res = await fetch(apiUrl('/tts/speak'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    })
    if (res.ok) {
      const data = await res.json()
      if (data.audio_url) {
        const audio = new Audio(`${data.audio_url}?t=${Date.now()}`)
        await audio.play()
        return
      }
    }
    // 503 (backend TTS disabled/unavailable) or unexpected payload -> fallback.
    browserSpeak(text)
  } catch (err) {
    console.error('Backend TTS failed, using browser speech', err)
    browserSpeak(text)
  }
}

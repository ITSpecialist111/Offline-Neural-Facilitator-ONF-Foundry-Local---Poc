// Central runtime configuration for the ONF frontend.
//
// The backend base URL is configurable via a Vite env var so the same build can
// target localhost (default), a LAN host, or a tunnel without code edits:
//
//   VITE_API_BASE=http://192.168.1.20:8000 npm run dev
//
// Defaults keep the offline-first, localhost-only behavior.

const rawBase = (import.meta.env.VITE_API_BASE || 'http://localhost:8000').replace(/\/$/, '')

export const API_BASE = rawBase

// Derive the matching ws:// or wss:// origin from the HTTP base.
export const WS_BASE = rawBase.replace(/^http/, 'ws')

// Build an absolute API URL from a path like '/chat'.
export const apiUrl = (path) => `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`

export const wsUrl = (path) => `${WS_BASE}${path.startsWith('/') ? path : `/${path}`}`

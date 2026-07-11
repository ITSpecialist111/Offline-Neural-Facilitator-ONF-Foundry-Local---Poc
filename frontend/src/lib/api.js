const configuredBase = import.meta.env.VITE_API_URL?.replace(/\/$/, '')
const fallbackHost = typeof window === 'undefined' ? '127.0.0.1' : window.location.hostname

export const API_BASE = configuredBase || `http://${fallbackHost}:8000`
export const WS_URL = API_BASE.replace(/^http/, 'ws') + '/ws/stream'

export async function api(path, options = {}) {
  const request = { ...options }
  const isForm = request.body instanceof FormData

  request.headers = {
    ...(isForm ? {} : request.body ? { 'Content-Type': 'application/json' } : {}),
    ...request.headers,
  }

  const response = await fetch(`${API_BASE}${path}`, request)
  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('application/json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    const detail = typeof payload === 'object' ? payload.detail : payload
    throw new Error(detail || `Request failed with status ${response.status}`)
  }

  return payload
}

export function audioUrl(path) {
  if (!path) return ''
  return path.startsWith('http') ? path : `${API_BASE}${path}`
}
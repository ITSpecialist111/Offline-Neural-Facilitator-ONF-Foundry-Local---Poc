import { useCallback, useEffect, useReducer, useRef, useState } from 'react'
import { api, WS_URL } from '../lib/api'

const EMPTY_STATE = {
  session: {
    id: 'ONF-LOCAL',
    status: 'starting',
    topic: 'Untitled session',
    started_at: new Date(0).toISOString(),
  },
  transcript: [],
  insights: [],
  decisions: [],
  actions: [],
  risks: [],
  metrics: {},
}

function appendUnique(items, item) {
  return items.some((candidate) => candidate.id === item.id) ? items : [...items, item]
}

function reducer(state, event) {
  switch (event.type) {
    case 'replace':
      return event.state
    case 'transcript':
      return { ...state, transcript: appendUnique(state.transcript, event.message) }
    case 'insight': {
      const insights = appendUnique(state.insights, event.insight)
      const risks = event.insight.kind === 'risk'
        ? appendUnique(state.risks, event.insight)
        : state.risks
      return { ...state, insights, risks }
    }
    case 'action':
      return { ...state, actions: appendUnique(state.actions, event.action) }
    case 'decision':
      return { ...state, decisions: appendUnique(state.decisions, event.decision) }
    case 'status':
      return { ...state, session: { ...state.session, status: event.status } }
    case 'title':
      return {
        ...state,
        session: { ...state.session, topic: event.topic, topic_source: event.source || 'conversation' },
      }
    default:
      return state
  }
}

export function useFacilitator() {
  const [state, dispatch] = useReducer(reducer, EMPTY_STATE)
  const [capabilities, setCapabilities] = useState({})
  const [connection, setConnection] = useState('connecting')
  const [lastError, setLastError] = useState('')
  const socketRef = useRef(null)
  const retryRef = useRef(0)

  const applyMessage = useCallback((message) => {
    if (message.type === 'session_state') {
      dispatch({ type: 'replace', state: message.state })
    } else if (message.type === 'transcript' && message.message) {
      dispatch({ type: 'transcript', message: message.message })
    } else if (message.type === 'insight' && message.insight) {
      dispatch({ type: 'insight', insight: message.insight })
    } else if (message.type === 'action' && message.action) {
      dispatch({ type: 'action', action: message.action })
    } else if (message.type === 'decision' && message.decision) {
      dispatch({ type: 'decision', decision: message.decision })
    } else if (message.type === 'session_status') {
      dispatch({ type: 'status', status: message.status })
    } else if (message.type === 'session_title' && message.topic) {
      dispatch({ type: 'title', topic: message.topic, source: message.source })
    } else if (message.type === 'error') {
      setLastError(message.message || 'A local capability returned an error.')
    }
  }, [])

  const refresh = useCallback(async () => {
    const payload = await api('/state')
    dispatch({ type: 'replace', state: payload.state })
    setCapabilities(payload.capabilities || {})
    return payload
  }, [])

  useEffect(() => {
    let active = true
    let reconnectTimer

    const connect = () => {
      if (!active) return
      setConnection('connecting')
      const socket = new WebSocket(WS_URL)
      socketRef.current = socket

      socket.onopen = () => {
        retryRef.current = 0
        setConnection('online')
        setLastError('')
        refresh().catch(() => undefined)
      }

      socket.onmessage = (event) => {
        try {
          applyMessage(JSON.parse(event.data))
        } catch {
          setLastError('The local event stream returned an unreadable message.')
        }
      }

      socket.onerror = () => socket.close()
      socket.onclose = () => {
        if (!active) return
        setConnection('offline')
        retryRef.current += 1
        const delay = Math.min(1000 * (2 ** retryRef.current), 10000)
        reconnectTimer = window.setTimeout(connect, delay)
      }
    }

    connect()
    return () => {
      active = false
      window.clearTimeout(reconnectTimer)
      socketRef.current?.close()
    }
  }, [applyMessage, refresh])

  useEffect(() => {
    const interval = window.setInterval(() => {
      refresh().catch(() => undefined)
    }, 15000)
    return () => window.clearInterval(interval)
  }, [refresh])

  const sendAudio = useCallback(async (blob) => {
    const socket = socketRef.current
    if (!socket || socket.readyState !== WebSocket.OPEN) return false
    socket.send(await blob.arrayBuffer())
    return true
  }, [])

  const run = useCallback(async (path, options) => {
    setLastError('')
    try {
      return await api(path, options)
    } catch (error) {
      setLastError(error.message)
      throw error
    }
  }, [])

  return {
    state,
    capabilities,
    connection,
    lastError,
    clearError: () => setLastError(''),
    refresh,
    run,
    sendAudio,
  }
}
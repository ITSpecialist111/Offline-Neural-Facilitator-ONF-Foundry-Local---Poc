import { useCallback, useEffect, useRef, useState } from 'react'

const SEGMENT_DURATION = 5000

function preferredMimeType() {
  const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus']
  return types.find((type) => MediaRecorder.isTypeSupported(type)) || ''
}

export function useSegmentRecorder(onSegment, onError) {
  const [isRecording, setIsRecording] = useState(false)
  const [segmentsSent, setSegmentsSent] = useState(0)
  const streamRef = useRef(null)
  const recorderRef = useRef(null)
  const timerRef = useRef(null)
  const recordingRef = useRef(false)
  const startSegmentRef = useRef(null)
  const segmentHandlerRef = useRef(onSegment)
  const errorHandlerRef = useRef(onError)

  useEffect(() => {
    segmentHandlerRef.current = onSegment
    errorHandlerRef.current = onError
  }, [onSegment, onError])

  const releaseStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
  }, [])

  const startSegment = useCallback(() => {
    if (!recordingRef.current || !streamRef.current) return
    const chunks = []
    const mimeType = preferredMimeType()
    const recorder = new MediaRecorder(streamRef.current, mimeType ? { mimeType } : undefined)
    recorderRef.current = recorder

    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) chunks.push(event.data)
    }

    recorder.onerror = (event) => {
      errorHandlerRef.current?.(event.error || new Error('Microphone recording failed.'))
    }

    recorder.onstop = async () => {
      window.clearTimeout(timerRef.current)
      if (chunks.length) {
        try {
          const blob = new Blob(chunks, { type: recorder.mimeType || 'audio/webm' })
          await segmentHandlerRef.current?.(blob)
          setSegmentsSent((count) => count + 1)
        } catch (error) {
          errorHandlerRef.current?.(error)
        }
      }

      if (recordingRef.current) {
        startSegmentRef.current?.()
      } else {
        releaseStream()
      }
    }

    recorder.start()
    timerRef.current = window.setTimeout(() => {
      if (recorder.state === 'recording') recorder.stop()
    }, SEGMENT_DURATION)
  }, [releaseStream])

  useEffect(() => {
    startSegmentRef.current = startSegment
  }, [startSegment])

  const start = useCallback(async () => {
    if (recordingRef.current) return
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      const error = new Error('This browser does not support local microphone capture.')
      errorHandlerRef.current?.(error)
      return
    }

    try {
      streamRef.current = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          channelCount: 1,
        },
      })
      recordingRef.current = true
      setSegmentsSent(0)
      setIsRecording(true)
      startSegment()
    } catch (error) {
      releaseStream()
      errorHandlerRef.current?.(error)
    }
  }, [releaseStream, startSegment])

  const stop = useCallback(() => {
    recordingRef.current = false
    setIsRecording(false)
    window.clearTimeout(timerRef.current)
    if (recorderRef.current?.state === 'recording') {
      recorderRef.current.stop()
    } else {
      releaseStream()
    }
  }, [releaseStream])

  useEffect(() => () => {
    recordingRef.current = false
    window.clearTimeout(timerRef.current)
    if (recorderRef.current?.state === 'recording') recorderRef.current.stop()
    releaseStream()
  }, [releaseStream])

  return { isRecording, segmentsSent, start, stop }
}
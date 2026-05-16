import { useCallback, useEffect, useRef, useState } from 'react'
import { useAuth } from '../context/AuthContext'

const WS_BASE = window.__WS_URL__ || import.meta.env.VITE_WS_URL || (
  (window.location.protocol === 'https:' ? 'wss' : 'ws') + '://' + window.location.host
)

export function useSimWebSocket(portfolioId) {
  const { token }                 = useAuth()
  const [state, setState]         = useState(null)
  const [month, setMonth]         = useState(0)
  const [lastEvents, setLastEvents] = useState([])
  const [connected, setConnected] = useState(false)
  const wsRef                     = useRef(null)
  const queueRef                  = useRef([])

  useEffect(() => {
    if (!token || !portfolioId) return

    const url = `${WS_BASE}/ws/${portfolioId}?token=${token}`
    const ws  = new WebSocket(url)
    wsRef.current = ws

    ws.onopen  = () => {
      setConnected(true)
      queueRef.current.forEach(msg => ws.send(JSON.stringify(msg)))
      queueRef.current = []
    }
    ws.onclose = () => setConnected(false)

    ws.onmessage = (e) => {
      const event = JSON.parse(e.data)

      if (event.type === 'connected') {
        setState(event.state)
        setMonth(event.month)
        return
      }
      if (event.type === 'month_complete' || event.type === 'state_update' || event.type === 'settings_updated') {
        setState(event.state)
        if (event.month !== undefined) setMonth(event.month)
      }

      setLastEvents(prev => [...prev.slice(-49), event])
    }

    return () => ws.close()
  }, [portfolioId, token])

  const send = useCallback((msg) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg))
    } else {
      queueRef.current.push(msg)
    }
  }, [])

  return { state, month, lastEvents, connected, send }
}

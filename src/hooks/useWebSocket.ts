import { useCallback, useEffect, useRef, useState } from 'react'

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected'

export interface WebSocketMessage {
  type: string
  [key: string]: any
}

export interface UseWebSocketReturn {
  connectionStatus: ConnectionStatus
  connect: (channel: string) => void
  disconnect: () => void
  sendMessage: (message: WebSocketMessage) => void
}

export function useWebSocket(
  onMessage: (message: WebSocketMessage) => void
): UseWebSocketReturn {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected')
  const wsRef = useRef<WebSocket | null>(null)
  const channelRef = useRef<string | null>(null)

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    channelRef.current = null
    setConnectionStatus('disconnected')
  }, [])

  const connect = useCallback((channel: string) => {
    // Close existing connection
    disconnect()

    channelRef.current = channel
    setConnectionStatus('connecting')

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/${channel}`

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket connected')
        setConnectionStatus('connected')
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          onMessage(message)
        } catch (error) {
          console.error('Error parsing message:', error)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setConnectionStatus('disconnected')
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setConnectionStatus('disconnected')
        wsRef.current = null
      }
    } catch (error) {
      console.error('WebSocket connection error:', error)
      setConnectionStatus('disconnected')
    }
  }, [disconnect, onMessage])

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected')
    }
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return {
    connectionStatus,
    connect,
    disconnect,
    sendMessage,
  }
}
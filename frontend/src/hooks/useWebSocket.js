import { useEffect, useRef } from 'react'
import { useCameraStore } from '../store'

export function useWebSocket() {
  const wsRef = useRef(null)
  const { setBulkCounts, setLiveCount, addCamera, removeCamera, updateCamera, setWsConnected } =
    useCameraStore()

  useEffect(() => {
    let reconnectTimer = null

    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
      const ws = new WebSocket(`${protocol}://${window.location.host}/ws/live`)
      wsRef.current = ws

      ws.onopen = () => {
        setWsConnected(true)
        console.log('[WS] connected')
      }

      ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data)
          switch (msg.type) {
            case 'initial_counts':
            case 'count_update':
              setBulkCounts(msg.counts || {})
              break
            case 'camera_update':
              if (msg.data?.people_count !== undefined)
                setLiveCount(msg.camera_id, msg.data.people_count)
              break
            case 'camera_added':
              if (msg.camera) addCamera(msg.camera)
              break
            case 'camera_removed':
              if (msg.camera_id) removeCamera(msg.camera_id)
              break
            case 'camera_updated':
              if (msg.camera_id) updateCamera(msg.camera_id, {})
              break
            case 'ping':
              ws.send(JSON.stringify({ type: 'pong' }))
              break
          }
        } catch {}
      }

      ws.onclose = () => {
        setWsConnected(false)
        console.log('[WS] disconnected — reconnecting in 4s')
        reconnectTimer = setTimeout(connect, 4000)
      }

      ws.onerror = () => ws.close()
    }

    connect()
    return () => {
      clearTimeout(reconnectTimer)
      wsRef.current?.close()
    }
  }, [])

  return wsRef
}

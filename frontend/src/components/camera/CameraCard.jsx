import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Users, MapPin, Crosshair, Trash2, RefreshCw, AlertCircle } from 'lucide-react'
import { useClock } from '../../hooks/useClock'
import { streamUrl } from '../../services/api'

export default function CameraCard({ camera, count = 0, onDelete }) {
  const [imgError, setImgError] = useState(false)
  const [retrying, setRetrying] = useState(false)
  const imgRef = useRef(null)
  const navigate = useNavigate()
  const time = useClock()

  const handleRetry = () => {
    setRetrying(true)
    setImgError(false)
    if (imgRef.current) {
      imgRef.current.src = ''
      setTimeout(() => {
        if (imgRef.current) imgRef.current.src = streamUrl(camera.id)
        setRetrying(false)
      }, 1000)
    }
  }

  return (
    <div
      className="card flex flex-col overflow-hidden animate-fade-in group hover:border-opacity-30 transition-all duration-200"
      style={{ borderColor: camera.is_connected ? 'rgba(0,255,157,0.2)' : 'rgba(255,255,255,0.07)' }}
    >
      {/* Video area */}
      <div className="relative bg-black" style={{ aspectRatio: '16/9' }}>
        {!imgError ? (
          <img
            ref={imgRef}
            src={streamUrl(camera.id)}
            alt={camera.name}
            className="w-full h-full object-cover"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center gap-3"
            style={{ background: 'var(--bg-secondary)' }}>
            <AlertCircle size={28} style={{ color: 'var(--text-muted)' }} />
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Stream unavailable</span>
            <button onClick={handleRetry} disabled={retrying}
              className="flex items-center gap-1.5 text-xs btn-ghost px-3 py-1.5">
              <RefreshCw size={12} className={retrying ? 'animate-spin' : ''} />
              Retry
            </button>
          </div>
        )}

        {/* Top-left: time */}
        <div className="absolute top-2 left-2 font-mono text-xs px-2 py-0.5 rounded"
          style={{ background: 'rgba(0,0,0,0.7)', color: 'var(--accent-cyan)' }}>
          {time.toLocaleTimeString()}
        </div>

        {/* Top-right: live status */}
        <div className="absolute top-2 right-2 flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium"
          style={{ background: 'rgba(0,0,0,0.7)', color: camera.is_connected ? 'var(--accent-green)' : 'var(--accent-red)' }}>
          <span className={camera.is_connected ? 'live-dot' : 'offline-dot'} />
          {camera.is_connected ? 'LIVE' : 'OFFLINE'}
        </div>

        {/* Bottom-left: people count */}
        <div className="absolute bottom-2 left-2 flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-bold"
          style={{ background: 'rgba(0,0,0,0.8)', color: 'var(--accent-green)' }}>
          <Users size={14} />
          {count}
        </div>

        {/* Hover actions */}
        <div className="absolute inset-0 flex items-center justify-center gap-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
          style={{ background: 'rgba(0,0,0,0.5)' }}>
          <button
            onClick={() => navigate(`/roi/${camera.id}`)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all"
            style={{ background: 'rgba(0,212,255,0.2)', color: 'var(--accent-cyan)', border: '1px solid rgba(0,212,255,0.4)' }}>
            <Crosshair size={12} />
            ROI
          </button>
          <button
            onClick={() => onDelete(camera.id)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all"
            style={{ background: 'rgba(255,61,107,0.2)', color: 'var(--accent-red)', border: '1px solid rgba(255,61,107,0.4)' }}>
            <Trash2 size={12} />
            Remove
          </button>
        </div>
      </div>

      {/* Info bar */}
      <div className="px-3 py-2.5 flex items-center justify-between"
        style={{ borderTop: '1px solid var(--border)' }}>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium truncate" style={{ color: 'var(--text-primary)' }}>
            {camera.name}
          </div>
          <div className="flex items-center gap-1 mt-0.5">
            <MapPin size={10} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
            <span className="text-xs truncate" style={{ color: 'var(--text-secondary)' }}>
              {camera.address}
            </span>
          </div>
        </div>
        <div className="ml-3 text-right shrink-0">
          <div className="font-mono text-lg font-bold leading-none" style={{ color: 'var(--accent-cyan)' }}>
            {count}
          </div>
          <div className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>people</div>
        </div>
      </div>
    </div>
  )
}

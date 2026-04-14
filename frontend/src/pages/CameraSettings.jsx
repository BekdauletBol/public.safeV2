import { useEffect, useState } from 'react'
import { Camera, Plus, Trash2, Crosshair, CheckCircle, XCircle } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { getCameras, deleteCamera, updateCamera } from '../services/api'
import { useCameraStore } from '../store'
import AddCameraModal from '../components/camera/AddCameraModal'
import toast from 'react-hot-toast'

const mono = { fontFamily: "'JetBrains Mono', monospace" }

export default function CameraSettings() {
  const { cameras, setCameras, addCamera, removeCamera, updateCamera: updateStore } = useCameraStore()
  const [showAdd, setShowAdd] = useState(false)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    getCameras()
      .then(({ data }) => setCameras(data))
      .catch(() => toast.error('Failed to load cameras'))
      .finally(() => setLoading(false))
  }, [])

  const handleDelete = async (id, name) => {
    if (!confirm(`Remove camera "${name}"?`)) return
    try {
      await deleteCamera(id)
      removeCamera(id)
      toast.success('Camera removed')
    } catch {
      toast.error('Failed to remove camera')
    }
  }

  const handleToggleActive = async (cam) => {
    try {
      await updateCamera(cam.id, { is_active: !cam.is_active })
      updateStore(cam.id, { is_active: !cam.is_active })
      toast.success(`Camera ${!cam.is_active ? 'activated' : 'deactivated'}`)
    } catch {
      toast.error('Failed to update camera')
    }
  }

  return (
    <div className="p-6 flex flex-col gap-6" style={mono}>
      <div className="flex items-start justify-between">
        <div>
          <h1 style={{ fontWeight: 300, fontSize: 22, color: '#fff', letterSpacing: '-0.01em' }}>
            camera management<span style={{ color: '#00d4ff' }}>.</span>
          </h1>
          <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)', marginTop: 4, letterSpacing: '0.06em' }}>
            configure streams, roi, and settings
          </p>
        </div>
        <button
          onClick={() => setShowAdd(true)}
          style={{
            ...mono, fontSize: 12, cursor: 'pointer',
            background: 'transparent', border: '1px solid rgba(0,212,255,0.4)',
            borderRadius: '3px', color: '#00d4ff', padding: '7px 14px',
            display: 'flex', alignItems: 'center', gap: 6, transition: 'all 0.15s',
          }}
          onMouseEnter={e => { e.currentTarget.style.background = 'rgba(0,212,255,0.06)'; e.currentTarget.style.borderColor = 'rgba(0,212,255,0.7)' }}
          onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.borderColor = 'rgba(0,212,255,0.4)' }}
        >
          <Plus size={13} /> add camera
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-6 h-6 rounded-full border animate-spin"
            style={{ borderColor: 'rgba(0,212,255,0.3)', borderTopColor: '#00d4ff' }} />
        </div>
      ) : cameras.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <Camera size={36} style={{ color: 'rgba(255,255,255,0.1)' }} />
          <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.3)', letterSpacing: '0.04em' }}>no cameras configured</p>
          <button
            onClick={() => setShowAdd(true)}
            style={{
              ...mono, fontSize: 12, cursor: 'pointer',
              background: 'transparent', border: '1px solid rgba(0,212,255,0.4)',
              borderRadius: '3px', color: '#00d4ff', padding: '7px 14px',
            }}
          >
            → add camera
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {cameras.map((cam) => (
            <div
              key={cam.id}
              style={{
                background: 'rgba(255,255,255,0.02)',
                border: '1px solid rgba(255,255,255,0.07)',
                borderRadius: '3px',
                padding: '12px 16px',
                display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap',
              }}
            >
              {/* ID */}
              <span style={{
                fontSize: 10, padding: '2px 7px', borderRadius: '2px',
                background: 'rgba(0,212,255,0.08)', color: '#00d4ff',
                letterSpacing: '0.06em', flexShrink: 0,
              }}>
                #{cam.id}
              </span>

              {/* Status dot */}
              <span style={{
                width: 6, height: 6, borderRadius: '50%', flexShrink: 0,
                background: cam.is_connected ? '#00ff9d' : 'rgba(255,255,255,0.2)',
                boxShadow: cam.is_connected ? '0 0 6px rgba(0,255,157,0.5)' : 'none',
              }} />

              {/* Info */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13, color: '#fff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {cam.name}
                </div>
                <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)', marginTop: 2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {cam.address}
                </div>
                <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.18)', marginTop: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {cam.stream_url}
                </div>
              </div>

              {/* Active toggle */}
              <button
                onClick={() => handleToggleActive(cam)}
                style={{
                  ...mono, background: 'none', border: 'none', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, flexShrink: 0,
                  color: cam.is_active ? '#00ff9d' : 'rgba(255,255,255,0.25)',
                }}
              >
                {cam.is_active
                  ? <CheckCircle size={13} style={{ color: '#00ff9d' }} />
                  : <XCircle size={13} />}
                {cam.is_active ? 'active' : 'inactive'}
              </button>

              {/* Actions */}
              <div className="flex gap-2 shrink-0">
                <button
                  onClick={() => navigate(`/roi/${cam.id}`)}
                  style={{
                    ...mono, fontSize: 11, cursor: 'pointer',
                    background: 'transparent', border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '3px', color: 'rgba(255,255,255,0.4)', padding: '5px 10px',
                    display: 'flex', alignItems: 'center', gap: 5,
                  }}
                >
                  <Crosshair size={12} /> roi
                </button>
                <button
                  onClick={() => handleDelete(cam.id, cam.name)}
                  style={{
                    ...mono, fontSize: 11, cursor: 'pointer',
                    background: 'transparent', border: '1px solid rgba(255,61,107,0.35)',
                    borderRadius: '3px', color: '#ff3d6b', padding: '5px 10px',
                    display: 'flex', alignItems: 'center', gap: 5,
                  }}
                >
                  <Trash2 size={12} /> remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showAdd && (
        <AddCameraModal
          onClose={() => setShowAdd(false)}
          onAdded={(cam) => { addCamera(cam); toast.success(`Camera #${cam.id} added`) }}
        />
      )}
    </div>
  )
}
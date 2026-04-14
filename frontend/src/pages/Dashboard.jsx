import { useEffect, useState } from 'react'
import { Plus, Users, Camera, Activity, AlertTriangle } from 'lucide-react'
import { getCameras, deleteCamera } from '../services/api'
import { useCameraStore } from '../store'
import CameraCard from '../components/camera/CameraCard'
import AddCameraModal from '../components/camera/AddCameraModal'
import toast from 'react-hot-toast'

const mono = { fontFamily: "'JetBrains Mono', monospace" }

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div style={{
      ...mono,
      background: 'rgba(255,255,255,0.02)',
      border: '1px solid rgba(255,255,255,0.07)',
      borderRadius: '3px',
      padding: '14px 16px',
      display: 'flex',
      alignItems: 'center',
      gap: '14px',
    }}>
      <div style={{
        width: 32, height: 32, borderRadius: '3px', flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: `${color}12`, border: `1px solid ${color}28`,
      }}>
        <Icon size={15} style={{ color }} />
      </div>
      <div>
        <div style={{ fontSize: 22, fontWeight: 300, color: '#fff', lineHeight: 1 }}>{value}</div>
        <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)', marginTop: 4, letterSpacing: '0.08em' }}>{label}</div>
      </div>
    </div>
  )
}

function getGridCols(count) {
  if (count === 1) return 'grid-cols-1'
  if (count === 2) return 'grid-cols-2'
  if (count <= 4) return 'grid-cols-2 xl:grid-cols-2'
  if (count <= 6) return 'grid-cols-2 xl:grid-cols-3'
  return 'grid-cols-2 xl:grid-cols-4'
}

export default function Dashboard() {
  const { cameras, setCameras, addCamera, removeCamera, liveCounts } = useCameraStore()
  const [showAdd, setShowAdd] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getCameras()
      .then(({ data }) => setCameras(data))
      .catch(() => toast.error('Failed to load cameras'))
      .finally(() => setLoading(false))
  }, [])

  const handleDelete = async (id) => {
    if (!confirm('Remove this camera?')) return
    try {
      await deleteCamera(id)
      removeCamera(id)
      toast.success('Camera removed')
    } catch {
      toast.error('Failed to remove camera')
    }
  }

  const handleAdded = (camera) => addCamera(camera)

  const totalPeople = Object.values(liveCounts).reduce((a, b) => a + b, 0)
  const activeCams = cameras.filter((c) => c.is_active).length
  const connectedCams = cameras.filter((c) => c.is_connected).length

  return (
    <div className="p-6 flex flex-col gap-6 min-h-full" style={mono}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 style={{ fontFamily: 'inherit', fontWeight: 300, fontSize: 22, color: '#fff', letterSpacing: '-0.01em' }}>
            surveillance dashboard<span style={{ color: '#00d4ff' }}>.</span>
          </h1>
          <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)', marginTop: 4, letterSpacing: '0.06em' }}>
            real-time monitoring · {cameras.length} camera{cameras.length !== 1 ? 's' : ''}
          </p>
        </div>
        <button
          onClick={() => setShowAdd(true)}
          style={{
            fontFamily: 'inherit', fontSize: 12, cursor: 'pointer',
            background: 'transparent', border: '1px solid rgba(0,212,255,0.4)',
            borderRadius: '3px', color: '#00d4ff', padding: '7px 14px',
            display: 'flex', alignItems: 'center', gap: 6,
            transition: 'all 0.15s',
          }}
          onMouseEnter={e => { e.currentTarget.style.background = 'rgba(0,212,255,0.06)'; e.currentTarget.style.borderColor = 'rgba(0,212,255,0.7)' }}
          onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.borderColor = 'rgba(0,212,255,0.4)' }}
        >
          <Plus size={13} /> add camera
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard icon={Users} label="people right now" value={totalPeople} color="#00d4ff" />
        <StatCard icon={Camera} label="total cameras" value={cameras.length} color="#00ff9d" />
        <StatCard icon={Activity} label="active streams" value={activeCams} color="#ffb830" />
        <StatCard icon={AlertTriangle} label="disconnected" value={cameras.length - connectedCams} color="#ff3d6b" />
      </div>

      {/* Camera grid */}
      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="w-6 h-6 rounded-full border animate-spin mx-auto mb-3"
              style={{ borderColor: 'rgba(0,212,255,0.3)', borderTopColor: '#00d4ff' }} />
            <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.25)', letterSpacing: '0.06em' }}>loading cameras...</p>
          </div>
        </div>
      ) : cameras.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Camera size={36} style={{ color: 'rgba(255,255,255,0.1)', margin: '0 auto 16px' }} />
            <h3 style={{ fontSize: 14, fontWeight: 400, color: 'rgba(255,255,255,0.4)', marginBottom: 6 }}>no cameras configured</h3>
            <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.2)', marginBottom: 16, letterSpacing: '0.04em' }}>
              add your first camera to start monitoring
            </p>
            <button
              onClick={() => setShowAdd(true)}
              style={{
                fontFamily: 'inherit', fontSize: 12, cursor: 'pointer',
                background: 'transparent', border: '1px solid rgba(0,212,255,0.4)',
                borderRadius: '3px', color: '#00d4ff', padding: '7px 14px',
              }}
            >
              → add camera
            </button>
          </div>
        </div>
      ) : (
        <div className={`grid gap-4 ${getGridCols(cameras.length)}`}>
          {cameras.map((cam) => (
            <CameraCard
              key={cam.id}
              camera={cam}
              count={liveCounts[cam.id] ?? cam.current_count ?? 0}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {showAdd && (
        <AddCameraModal onClose={() => setShowAdd(false)} onAdded={handleAdded} />
      )}
    </div>
  )
}
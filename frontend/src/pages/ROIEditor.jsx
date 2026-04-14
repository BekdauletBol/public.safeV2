import { useEffect, useRef, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Save, RotateCcw, ArrowLeft, Crosshair } from 'lucide-react'
import { getCamera, getRoi, setRoi, snapshotUrl } from '../services/api'
import toast from 'react-hot-toast'

const HANDLE_SIZE = 10
const mono = { fontFamily: "'JetBrains Mono', monospace" }

export default function ROIEditor() {
  const { cameraId } = useParams()
  const navigate = useNavigate()
  const canvasRef = useRef(null)
  const [camera, setCamera] = useState(null)
  const [roi, setRoiState] = useState({ x: 0.1, y: 0.1, width: 0.8, height: 0.8 })
  const [dragging, setDragging] = useState(null)
  const [imgLoaded, setImgLoaded] = useState(false)
  const imgRef = useRef(new Image())
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    const id = Number(cameraId)
    Promise.all([getCamera(id), getRoi(id)]).then(([c, r]) => {
      setCamera(c.data)
      if (r.data?.is_active) {
        setRoiState({ x: r.data.x, y: r.data.y, width: r.data.width, height: r.data.height })
      }
    })
    const img = imgRef.current
    img.src = snapshotUrl(id) + '?t=' + Date.now()
    img.onload = () => setImgLoaded(true)
    img.onerror = () => setImgLoaded(false)
  }, [cameraId])

  const draw = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const { width: cw, height: ch } = canvas
    ctx.clearRect(0, 0, cw, ch)

    if (imgLoaded) {
      ctx.drawImage(imgRef.current, 0, 0, cw, ch)
    } else {
      ctx.fillStyle = '#0a0b0d'
      ctx.fillRect(0, 0, cw, ch)
      ctx.fillStyle = 'rgba(255,255,255,0.15)'
      ctx.font = '12px JetBrains Mono'
      ctx.textAlign = 'center'
      ctx.fillText('no snapshot available', cw / 2, ch / 2)
    }

    const rx = roi.x * cw, ry = roi.y * ch
    const rw = roi.width * cw, rh = roi.height * ch

    ctx.fillStyle = 'rgba(0,0,0,0.6)'
    ctx.fillRect(0, 0, cw, ry)
    ctx.fillRect(0, ry + rh, cw, ch - ry - rh)
    ctx.fillRect(0, ry, rx, rh)
    ctx.fillRect(rx + rw, ry, cw - rx - rw, rh)

    ctx.strokeStyle = '#00d4ff'
    ctx.lineWidth = 1.5
    ctx.setLineDash([5, 3])
    ctx.strokeRect(rx, ry, rw, rh)
    ctx.setLineDash([])

    const handles = getHandles(rx, ry, rw, rh)
    handles.forEach(([hx, hy]) => {
      ctx.fillStyle = '#00d4ff'
      ctx.fillRect(hx - HANDLE_SIZE / 2, hy - HANDLE_SIZE / 2, HANDLE_SIZE, HANDLE_SIZE)
    })

    ctx.fillStyle = 'rgba(0,0,0,0.75)'
    ctx.fillRect(rx, ry - 20, 72, 18)
    ctx.fillStyle = '#00d4ff'
    ctx.font = '10px JetBrains Mono'
    ctx.textAlign = 'left'
    ctx.fillText('roi zone', rx + 5, ry - 6)
  }, [roi, imgLoaded])

  useEffect(() => { draw() }, [draw])

  function getHandles(rx, ry, rw, rh) {
    return [
      [rx, ry], [rx + rw, ry], [rx + rw, ry + rh], [rx, ry + rh],
      [rx + rw / 2, ry], [rx + rw, ry + rh / 2],
      [rx + rw / 2, ry + rh], [rx, ry + rh / 2],
    ]
  }

  const hitHandle = (mx, my, cw, ch) => {
    const rx = roi.x * cw, ry = roi.y * ch, rw = roi.width * cw, rh = roi.height * ch
    const handles = getHandles(rx, ry, rw, rh)
    const labels = ['tl', 'tr', 'br', 'bl', 'tm', 'rm', 'bm', 'lm']
    for (let i = 0; i < handles.length; i++) {
      const [hx, hy] = handles[i]
      if (Math.abs(mx - hx) < HANDLE_SIZE && Math.abs(my - hy) < HANDLE_SIZE) return labels[i]
    }
    if (mx > rx && mx < rx + rw && my > ry && my < ry + rh) return 'move'
    return null
  }

  const onMouseDown = (e) => {
    const canvas = canvasRef.current
    const rect = canvas.getBoundingClientRect()
    const mx = e.clientX - rect.left, my = e.clientY - rect.top
    const hit = hitHandle(mx, my, canvas.width, canvas.height)
    if (hit) setDragging({ type: hit, startX: mx, startY: my, startRoi: { ...roi } })
  }

  const onMouseMove = (e) => {
    if (!dragging) return
    const canvas = canvasRef.current
    const rect = canvas.getBoundingClientRect()
    const mx = e.clientX - rect.left, my = e.clientY - rect.top
    const dx = (mx - dragging.startX) / canvas.width
    const dy = (my - dragging.startY) / canvas.height
    const { x, y, width, height } = dragging.startRoi
    let newRoi = { ...dragging.startRoi }
    const clamp = (v, min, max) => Math.min(max, Math.max(min, v))
    switch (dragging.type) {
      case 'move': newRoi.x = clamp(x + dx, 0, 1 - width); newRoi.y = clamp(y + dy, 0, 1 - height); break
      case 'tl': newRoi.x = clamp(x + dx, 0, x + width - 0.05); newRoi.y = clamp(y + dy, 0, y + height - 0.05); newRoi.width = width - (newRoi.x - x); newRoi.height = height - (newRoi.y - y); break
      case 'tr': newRoi.y = clamp(y + dy, 0, y + height - 0.05); newRoi.width = clamp(width + dx, 0.05, 1 - x); newRoi.height = height - (newRoi.y - y); break
      case 'br': newRoi.width = clamp(width + dx, 0.05, 1 - x); newRoi.height = clamp(height + dy, 0.05, 1 - y); break
      case 'bl': newRoi.x = clamp(x + dx, 0, x + width - 0.05); newRoi.width = width - (newRoi.x - x); newRoi.height = clamp(height + dy, 0.05, 1 - y); break
      case 'tm': newRoi.y = clamp(y + dy, 0, y + height - 0.05); newRoi.height = height - (newRoi.y - y); break
      case 'bm': newRoi.height = clamp(height + dy, 0.05, 1 - y); break
      case 'lm': newRoi.x = clamp(x + dx, 0, x + width - 0.05); newRoi.width = width - (newRoi.x - x); break
      case 'rm': newRoi.width = clamp(width + dx, 0.05, 1 - x); break
    }
    setRoiState(newRoi)
  }

  const onMouseUp = () => setDragging(null)

  const handleSave = async () => {
    setSaving(true)
    try {
      await setRoi(Number(cameraId), { camera_id: Number(cameraId), ...roi, is_active: true })
      toast.success('ROI saved')
    } catch {
      toast.error('Failed to save ROI')
    } finally {
      setSaving(false)
    }
  }

  const handleReset = () => setRoiState({ x: 0.05, y: 0.05, width: 0.9, height: 0.9 })

  const ghostBtn = {
    ...mono, fontSize: 12, cursor: 'pointer',
    background: 'transparent', border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '3px', color: 'rgba(255,255,255,0.4)', padding: '7px 12px',
    display: 'flex', alignItems: 'center', gap: 5,
  }

  return (
    <div className="p-6 flex flex-col gap-5" style={mono}>
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/cameras')} style={ghostBtn}>
          <ArrowLeft size={13} /> back
        </button>
        <div>
          <h1 style={{ fontWeight: 300, fontSize: 20, color: '#fff', letterSpacing: '-0.01em' }}>
            roi editor<span style={{ color: '#00d4ff' }}>.</span>
          </h1>
          {camera && (
            <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)', marginTop: 2, letterSpacing: '0.04em' }}>
              {camera.name} · {camera.address}
            </p>
          )}
        </div>
      </div>

      <div style={{
        background: 'rgba(255,255,255,0.02)',
        border: '1px solid rgba(255,255,255,0.07)',
        borderRadius: '3px', padding: 16,
      }}>
        <div className="flex items-center gap-2 mb-3">
          <Crosshair size={12} style={{ color: '#00d4ff' }} />
          <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', letterSpacing: '0.06em' }}>
            drag the rectangle to define the counting zone
          </span>
        </div>
        <canvas
          ref={canvasRef}
          width={960}
          height={540}
          style={{
            width: '100%', borderRadius: '3px', display: 'block',
            maxHeight: '60vh', background: '#000',
            cursor: dragging ? 'grabbing' : 'crosshair',
          }}
          onMouseDown={onMouseDown}
          onMouseMove={onMouseMove}
          onMouseUp={onMouseUp}
          onMouseLeave={onMouseUp}
        />
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <div style={{
          ...mono, fontSize: 11, padding: '6px 12px',
          background: 'rgba(0,212,255,0.06)', border: '1px solid rgba(0,212,255,0.15)',
          borderRadius: '3px', color: 'rgba(0,212,255,0.8)', letterSpacing: '0.04em',
        }}>
          x: {roi.x.toFixed(3)} · y: {roi.y.toFixed(3)} · w: {roi.width.toFixed(3)} · h: {roi.height.toFixed(3)}
        </div>
        <div style={{ flex: 1 }} />
        <button onClick={handleReset} style={ghostBtn}>
          <RotateCcw size={12} /> reset
        </button>
        <button
          onClick={handleSave}
          disabled={saving}
          style={{
            ...mono, fontSize: 12, cursor: saving ? 'not-allowed' : 'pointer',
            opacity: saving ? 0.6 : 1,
            background: 'transparent', border: '1px solid rgba(0,212,255,0.4)',
            borderRadius: '3px', color: '#00d4ff', padding: '7px 14px',
            display: 'flex', alignItems: 'center', gap: 5, transition: 'all 0.15s',
          }}
        >
          <Save size={12} /> {saving ? 'saving...' : 'save roi'}
        </button>
      </div>
    </div>
  )
}
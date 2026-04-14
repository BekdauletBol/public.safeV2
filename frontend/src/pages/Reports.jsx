import { useEffect, useState } from 'react'
import { FileText, Download, RefreshCw, Clock, CheckCircle, AlertCircle, Loader } from 'lucide-react'
import { getReports, generateReport } from '../services/api'
import { format, parseISO } from 'date-fns'
import toast from 'react-hot-toast'

const mono = { fontFamily: "'JetBrains Mono', monospace" }

const StatusIcon = ({ status }) => {
  if (status === 'ready') return <CheckCircle size={12} style={{ color: '#00ff9d' }} />
  if (status === 'failed') return <AlertCircle size={12} style={{ color: '#ff3d6b' }} />
  return <Loader size={12} className="animate-spin" style={{ color: '#ffb830' }} />
}

export default function Reports() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  const fetchReports = () => {
    setLoading(true)
    getReports()
      .then(({ data }) => setReports(data))
      .catch(() => toast.error('Failed to load reports'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchReports() }, [])

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      await generateReport()
      toast.success('Report generated successfully')
      fetchReports()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Report generation failed')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="p-6 flex flex-col gap-6" style={mono}>
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 style={{ fontWeight: 300, fontSize: 22, color: '#fff', letterSpacing: '-0.01em' }}>
            reports<span style={{ color: '#00d4ff' }}>.</span>
          </h1>
          <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)', marginTop: 4, letterSpacing: '0.06em' }}>
            auto-generated every sunday at 23:59 · pdf & csv
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchReports}
            style={{
              ...mono, fontSize: 11, cursor: 'pointer',
              background: 'transparent', border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '3px', color: 'rgba(255,255,255,0.4)', padding: '7px 12px',
              display: 'flex', alignItems: 'center', gap: 5,
            }}
          >
            <RefreshCw size={12} /> refresh
          </button>
          <button
            onClick={handleGenerate}
            disabled={generating}
            style={{
              ...mono, fontSize: 11, cursor: generating ? 'not-allowed' : 'pointer',
              opacity: generating ? 0.6 : 1,
              background: 'transparent', border: '1px solid rgba(0,212,255,0.4)',
              borderRadius: '3px', color: '#00d4ff', padding: '7px 12px',
              display: 'flex', alignItems: 'center', gap: 5, transition: 'all 0.15s',
            }}
          >
            {generating
              ? <><Loader size={12} className="animate-spin" /> generating...</>
              : <><FileText size={12} /> generate now</>}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-6 h-6 rounded-full border animate-spin"
            style={{ borderColor: 'rgba(0,212,255,0.3)', borderTopColor: '#00d4ff' }} />
        </div>
      ) : reports.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <FileText size={36} style={{ color: 'rgba(255,255,255,0.1)' }} />
          <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.3)', letterSpacing: '0.04em' }}>no reports yet</p>
          <button
            onClick={handleGenerate}
            style={{
              ...mono, fontSize: 12, cursor: 'pointer',
              background: 'transparent', border: '1px solid rgba(0,212,255,0.4)',
              borderRadius: '3px', color: '#00d4ff', padding: '7px 14px',
            }}
          >
            → generate first report
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {reports.map((r) => (
            <div
              key={r.id}
              style={{
                background: 'rgba(255,255,255,0.02)',
                border: '1px solid rgba(255,255,255,0.07)',
                borderRadius: '3px',
                padding: '14px 16px',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                gap: 12, flexWrap: 'wrap',
              }}
            >
              <div className="flex items-start gap-3">
                <div style={{
                  width: 32, height: 32, borderRadius: '3px', flexShrink: 0,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  background: 'rgba(0,212,255,0.07)', border: '1px solid rgba(0,212,255,0.15)',
                }}>
                  <FileText size={14} style={{ color: '#00d4ff' }} />
                </div>
                <div>
                  <div style={{ fontSize: 12, color: '#fff' }}>{r.title}</div>
                  <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)', marginTop: 3, display: 'flex', alignItems: 'center', gap: 5 }}>
                    <Clock size={9} />
                    {r.period_start ? format(parseISO(r.period_start), 'MMM d') : '?'}
                    {' – '}
                    {r.period_end ? format(parseISO(r.period_end), 'MMM d, yyyy') : '?'}
                  </div>
                  <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.2)', marginTop: 2 }}>
                    created: {r.created_at ? format(parseISO(r.created_at), 'MMM d, yyyy HH:mm') : '?'}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: 'rgba(255,255,255,0.35)', textTransform: 'lowercase' }}>
                  <StatusIcon status={r.status} />
                  {r.status}
                </div>
                {r.status === 'ready' && r.download_url && (
                  <a
                    href={r.download_url}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      ...mono, fontSize: 11, textDecoration: 'none',
                      background: 'transparent', border: '1px solid rgba(0,212,255,0.4)',
                      borderRadius: '3px', color: '#00d4ff', padding: '5px 10px',
                      display: 'flex', alignItems: 'center', gap: 5,
                    }}
                  >
                    <Download size={11} /> download pdf
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

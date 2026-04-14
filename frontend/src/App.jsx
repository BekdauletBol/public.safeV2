import { Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/ui/Layout'
import Dashboard from './pages/Dashboard'
import Analytics from './pages/Analytics'
import Reports from './pages/Reports'
import CameraSettings from './pages/CameraSettings'
import Login from './pages/Login'
import ROIEditor from './pages/ROIEditor'
import { useAuthStore } from './store'
import { useWebSocket } from './hooks/useWebSocket'

function ProtectedRoute({ children }) {
  const { token } = useAuthStore()
  return token ? children : <Navigate to="/login" replace />
}

function AppInner() {
  useWebSocket()
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/cameras" element={<CameraSettings />} />
        <Route path="/roi/:cameraId" element={<ROIEditor />} />
      </Routes>
    </Layout>
  )
}

export default function App() {
  const { token } = useAuthStore()
  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#141d2f',
            color: '#e8ecf4',
            border: '1px solid rgba(255,255,255,0.07)',
            fontFamily: 'DM Sans, sans-serif',
            fontSize: '14px',
          },
        }}
      />
      <Routes>
        <Route path="/login" element={token ? <Navigate to="/" replace /> : <Login />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <AppInner />
            </ProtectedRoute>
          }
        />
      </Routes>
    </>
  )
}

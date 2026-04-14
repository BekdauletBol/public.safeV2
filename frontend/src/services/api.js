import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  const raw = localStorage.getItem('auth-storage')
  if (raw) {
    const { state } = JSON.parse(raw)
    if (state?.token) config.headers.Authorization = `Bearer ${state.token}`
  }
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('auth-storage')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// Auth
export const login = (data) => api.post('/auth/login', data)
export const register = (data) => api.post('/auth/register', data)

// Cameras
export const getCameras = () => api.get('/cameras/')
export const getCamera = (id) => api.get(`/cameras/${id}`)
export const createCamera = (data) => api.post('/cameras/', data)
export const updateCamera = (id, data) => api.put(`/cameras/${id}`, data)
export const deleteCamera = (id) => api.delete(`/cameras/${id}`)

// Analytics
export const getRealtimeCounts = () => api.get('/analytics/realtime')
export const getCameraHourly = (id, hours = 24) => api.get(`/analytics/camera/${id}/hourly?hours=${hours}`)
export const getCameraDaily = (id, days = 7) => api.get(`/analytics/camera/${id}/daily?days=${days}`)
export const getCameraPeaks = (id) => api.get(`/analytics/camera/${id}/peaks`)
export const getWeeklySummary = () => api.get('/analytics/summary/weekly')

// Reports
export const getReports = () => api.get('/reports/')
export const generateReport = () => api.post('/reports/generate')
export const getReport = (id) => api.get(`/reports/${id}`)
export const downloadReportUrl = (id) => `/api/reports/${id}/download`

// ROI
export const getRoi = (id) => api.get(`/roi/${id}`)
export const setRoi = (id, data) => api.post(`/roi/${id}`, data)
export const deleteRoi = (id) => api.delete(`/roi/${id}`)

// Stream URL
export const streamUrl = (id) => `/api/streams/${id}/feed`
export const snapshotUrl = (id) => `/api/streams/${id}/snapshot`

export default api

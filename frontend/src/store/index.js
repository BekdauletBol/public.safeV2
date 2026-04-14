import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAuthStore = create(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: 'auth-storage' }
  )
)

export const useCameraStore = create((set, get) => ({
  cameras: [],
  liveCounts: {},
  wsConnected: false,

  setCameras: (cameras) => set({ cameras }),

  addCamera: (camera) =>
    set((s) => ({
      cameras: s.cameras.some((c) => c.id === camera.id)
        ? s.cameras
        : [...s.cameras, camera],
    })),

  removeCamera: (id) =>
    set((s) => ({ cameras: s.cameras.filter((c) => c.id !== id) })),

  updateCamera: (id, data) =>
    set((s) => ({
      cameras: s.cameras.map((c) => (c.id === id ? { ...c, ...data } : c)),
    })),

  setLiveCount: (cameraId, count) =>
    set((s) => ({ liveCounts: { ...s.liveCounts, [cameraId]: count } })),

  setBulkCounts: (counts) => set({ liveCounts: counts }),

  setWsConnected: (v) => set({ wsConnected: v }),
}))

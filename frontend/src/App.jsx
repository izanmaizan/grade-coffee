import { useState, useCallback, createContext, useContext } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Toast from './components/Toast'
import AnalyzePage from './pages/AnalyzePage'
import HistoryPage from './pages/HistoryPage'
import PricesPage from './pages/PricesPage'

// Context untuk toast
const ToastContext = createContext(null)
export const useToast = () => {
  const ctx = useContext(ToastContext)
  if (!ctx) {
    // Fallback biar tidak crash: return function kosong
    console.warn('useToast dipanggil di luar ToastProvider')
    return () => {}
  }
  return ctx
}

function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const addToast = useCallback((message, type = 'success') => {
    const id = Date.now() + Math.random()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 3500)
  }, [])

  return (
    <ToastContext.Provider value={addToast}>
      {children}
      <div className="fixed top-5 right-5 z-50 flex flex-col gap-2 pointer-events-none">
        {toasts.map(t => (
          <div key={t.id} className="pointer-events-auto">
            <Toast
              message={t.message}
              type={t.type}
              onClose={() => setToasts(prev => prev.filter(x => x.id !== t.id))}
            />
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export default function App() {
  return (
    <ToastProvider>
      <Layout>
        <Routes>
          <Route path="/" element={<AnalyzePage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/prices" element={<PricesPage />} />
        </Routes>
      </Layout>
    </ToastProvider>
  )
}
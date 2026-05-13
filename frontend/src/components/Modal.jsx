import { X } from 'lucide-react'
import { useEffect } from 'react'

export default function Modal({ isOpen, onClose, title, children, maxWidth = 'max-w-lg' }) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [isOpen])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in">
      <div className="absolute inset-0 bg-coffee-950/40 backdrop-blur-sm" onClick={onClose} />
      <div className={`relative bg-white rounded-2xl shadow-elevated w-full ${maxWidth} animate-scale-in overflow-hidden`}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-coffee-100">
          <h3 className="text-lg font-semibold text-coffee-900 font-display">{title}</h3>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-coffee-100 transition-colors">
            <X size={20} className="text-coffee-500" />
          </button>
        </div>
        <div className="px-6 py-5">{children}</div>
      </div>
    </div>
  )
}
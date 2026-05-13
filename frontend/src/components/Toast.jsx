import { X, CheckCircle, AlertCircle, Info } from 'lucide-react'

const icons = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
}

const colors = {
  success: 'bg-bean-600 text-white',
  error: 'bg-red-500 text-white',
  info: 'bg-slate-700 text-white',
}

export default function Toast({ message, type = 'success', onClose }) {
  const Icon = icons[type] || Info
  return (
    <div className={`toast-enter flex items-center gap-3 px-4 py-3 rounded-xl shadow-elevated ${colors[type]} min-w-[280px] max-w-sm`}>
      <Icon size={18} />
      <span className="text-sm font-medium flex-1">{message}</span>
      <button onClick={onClose} className="opacity-70 hover:opacity-100 transition-opacity">
        <X size={16} />
      </button>
    </div>
  )
}
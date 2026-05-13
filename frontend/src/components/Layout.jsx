import { Link, useLocation } from 'react-router-dom'
import { Beaker, History, DollarSign, Coffee, Sparkles } from 'lucide-react'

const nav = [
  { to: '/', icon: Beaker, label: 'Analisa', desc: 'Upload & deteksi' },
  { to: '/history', icon: History, label: 'Riwayat', desc: 'Hasil analisa' },
  { to: '/prices', icon: DollarSign, label: 'Harga', desc: 'Kelola grade' },
]

export default function Layout({ children }) {
  const { pathname } = useLocation()

  return (
    <div className="flex h-screen overflow-hidden bg-coffee-50/30">
      {/* Sidebar */}
      <aside className="sidebar-glass w-64 flex-shrink-0 flex flex-col">
        {/* Logo */}
        <div className="px-5 pt-6 pb-4">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-bean-600 flex items-center justify-center shadow-soft group-hover:bg-bean-700 transition-colors">
              <Coffee size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-coffee-900 leading-tight">Green Bean</h1>
              <p className="text-xs text-coffee-500">Grading System</p>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-2 space-y-1">
          {nav.map(item => {
            const isActive = pathname === item.to
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 group
                  ${isActive
                    ? 'bg-bean-600 text-white shadow-soft'
                    : 'text-coffee-700 hover:bg-coffee-100/70 hover:text-coffee-900'
                  }`}
              >
                <item.icon size={18} className={isActive ? '' : 'text-coffee-400 group-hover:text-coffee-700 transition-colors'} />
                <div>
                  <div className="text-sm">{item.label}</div>
                  <div className={`text-xs ${isActive ? 'text-bean-200' : 'text-coffee-400'}`}>{item.desc}</div>
                </div>
                {isActive && (
                  <div className="ml-auto w-1.5 h-1.5 rounded-full bg-white/60" />
                )}
              </Link>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-coffee-200/50">
          <div className="flex items-center gap-2 text-xs text-coffee-500">
            <Sparkles size={12} />
            <span>AI-Powered Grading</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-5xl mx-auto px-6 py-8">
          {children}
        </div>
      </main>
    </div>
  )
}
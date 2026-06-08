import { Component } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

/**
 * Error boundary global (#16).
 * Menangkap error render di subtree agar satu komponen yang crash tidak
 * membuat seluruh aplikasi blank, dan menampilkan fallback yang ramah.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    // Di production sebaiknya dikirim ke layanan monitoring (Sentry, dsb.)
    console.error('ErrorBoundary menangkap error:', error, info)
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null })
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          role="alert"
          className="min-h-screen flex items-center justify-center p-6 bg-coffee-50/30"
        >
          <div className="card p-8 max-w-md text-center">
            <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-red-100 flex items-center justify-center">
              <AlertTriangle size={26} className="text-red-500" />
            </div>
            <h2 className="text-xl font-bold text-coffee-900 mb-2">
              Terjadi kesalahan
            </h2>
            <p className="text-sm text-coffee-500 mb-5">
              Maaf, ada yang tidak beres saat menampilkan halaman ini. Coba muat
              ulang. Jika masih bermasalah, hubungi administrator.
            </p>
            <button onClick={this.handleReload} className="btn-primary mx-auto">
              <RefreshCw size={16} /> Muat Ulang
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

import { useState, useRef, useCallback, useEffect } from 'react'
import {
  Upload, X, Loader2, Image, CheckCircle2, AlertTriangle, Info,
  Download, RefreshCw, Eye, EyeOff, ChevronDown, ChevronUp,
  Camera, CameraOff,
} from 'lucide-react'
import { analyzeApi, formatRupiah } from '../client'
import { useToast } from '../App'

const GRADE_COLORS = {
  GRADE_1: '#10b981',
  GRADE_2: '#3b82f6',
  GRADE_3: '#f59e0b',
  GRADE_4: '#ef4444',
  GRADE_5: '#6b7280',
}

const DEFECT_COLORS = [
  '#f87171', '#fb923c', '#fbbf24', '#a3e635', '#34d399', '#22d3ee',
  '#60a5fa', '#818cf8', '#c084fc', '#e879f9', '#fb7185', '#f97316',
  '#facc15', '#4ade80', '#2dd4bf', '#38bdf8',
]

const WEIGHT_PRESETS = [50, 100, 350, 500]

/* ---- Helper: dataURL ke File ---- */
function dataURLtoFile(dataurl, filename) {
  const arr = dataurl.split(',')
  const mime = arr[0].match(/:(.*?);/)[1]
  const bstr = atob(arr[1])
  let n = bstr.length
  const u8arr = new Uint8Array(n)
  while (n--) u8arr[n] = bstr.charCodeAt(n)
  return new File([u8arr], filename, { type: mime })
}

export default function AnalyzePage() {
  const addToast = useToast()
  const [image, setImage] = useState(null)
  const [preview, setPreview] = useState(null)
  const [weight, setWeight] = useState(350)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [showOverlay, setShowOverlay] = useState(true)
  const [showDetectionList, setShowDetectionList] = useState(false)
  const [highlightedIndex, setHighlightedIndex] = useState(null)
  const [imageScale, setImageScale] = useState({ x: 1, y: 1 })

  /* ---- Filter bounding box per kelas ---- */
  const [activeFilterClass, setActiveFilterClass] = useState(null) // string atau null

  /* ---- Kamera ---- */
  const [cameraActive, setCameraActive] = useState(false)
  const [cameraStream, setCameraStream] = useState(null)
  const videoRef = useRef(null)

  const fileInputRef = useRef(null)
  const imageContainerRef = useRef(null)
  const mainImageRef = useRef(null)

  /* ---- Mulai Kamera ---- */
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } },
      })
      setCameraStream(stream)
      setCameraActive(true)
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
    } catch (err) {
      console.error('Kamera gagal:', err)
      addToast('Tidak bisa mengakses kamera.', 'error')
    }
  }

  /* ---- Hentikan Kamera ---- */
  const stopCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop())
      setCameraStream(null)
    }
    setCameraActive(false)
  }

  /* ---- Ambil Snapshot ---- */
  const captureSnapshot = () => {
    const video = videoRef.current
    if (!video) return
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    canvas.getContext('2d').drawImage(video, 0, 0)
    const dataURL = canvas.toDataURL('image/jpeg', 0.9)
    const file = dataURLtoFile(dataURL, `snapshot_${Date.now()}.jpg`)
    handleFile(file)
    stopCamera()
  }

  /* ---- Tangani File (sama seperti sebelumnya) ---- */
  const handleFile = useCallback((file) => {
    if (!file) return
    const allowed = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!allowed.includes(ext)) {
      setError('Format tidak didukung. Gunakan: ' + allowed.join(', '))
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('Ukuran gambar maksimal 10MB')
      return
    }
    setImage(file)
    const url = URL.createObjectURL(file)
    setPreview(url)
    setResult(null)
    setError(null)
    setShowOverlay(true)
    setShowDetectionList(false)
    setHighlightedIndex(null)
    setActiveFilterClass(null)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0]
    handleFile(file)
  }, [handleFile])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!image) {
      setError('Pilih gambar terlebih dahulu')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const data = await analyzeApi.analyze(image, weight)
      setResult(data)
      addToast('Analisa berhasil!', 'success')
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Gagal menganalisa'
      setError(msg)
      addToast(msg, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    if (preview) URL.revokeObjectURL(preview)
    setImage(null)
    setPreview(null)
    setResult(null)
    setError(null)
    setShowOverlay(true)
    setShowDetectionList(false)
    setHighlightedIndex(null)
    setActiveFilterClass(null)
    stopCamera()
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  /* ---- Skala overlay ---- */
  const updateScale = useCallback(() => {
    const imgEl = mainImageRef.current
    if (imgEl && imgEl.naturalWidth) {
      setImageScale({
        x: imgEl.offsetWidth / imgEl.naturalWidth,
        y: imgEl.offsetHeight / imgEl.naturalHeight,
      })
    }
  }, [])

  useEffect(() => {
    window.addEventListener('resize', updateScale)
    return () => window.removeEventListener('resize', updateScale)
  }, [updateScale])

  const handleImageLoad = () => updateScale()

  // Bersihkan stream saat unmount
  useEffect(() => {
    return () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop())
      }
    }
  }, [cameraStream])

  /* ---- Filter deteksi berdasarkan kelas aktif ---- */
  const detections = result?.detections || []
  const filteredDetections = activeFilterClass
    ? detections.filter(d => d.class_name === activeFilterClass)
    : detections

  const hasDetections = detections.length > 0
  const summary = result?.detection_summary || {}
  const detectedClasses = Object.keys(summary)

  return (
    <div className="animate-fade-in space-y-8">
      {/* Header */}
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-display font-bold text-coffee-900">
          Analisa <span className="text-bean-600">Green Bean</span>
        </h2>
        <p className="text-coffee-500 max-w-md mx-auto">
          Unggah gambar sampel kopi dan dapatkan grade + estimasi harga secara instan
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Upload Section */}
        <div className="lg:col-span-2 space-y-4">
          <div className="card p-6 space-y-5">
            <h3 className="font-semibold text-coffee-800 flex items-center gap-2">
              <Upload size={18} className="text-bean-600" />
              Upload Sampel
            </h3>

            {/* Drop Zone / Preview */}
            {!preview ? (
              <div
                className={`drop-zone border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300
                  ${dragOver ? 'border-bean-400 bg-bean-50/50 scale-[1.02]' : 'border-coffee-200 hover:border-bean-300 hover:bg-bean-50/30'}`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="w-14 h-14 mx-auto mb-3 rounded-2xl bg-bean-100 flex items-center justify-center">
                  <Image size={24} className="text-bean-600" />
                </div>
                <p className="text-sm font-medium text-coffee-800 mb-1">Seret & lepas gambar di sini</p>
                <p className="text-xs text-coffee-400">atau klik untuk pilih file</p>
                <p className="text-xs text-coffee-300 mt-3">JPG, PNG, WebP • Maks 10MB</p>
              </div>
            ) : (
              <div className="relative rounded-2xl overflow-hidden bg-coffee-100">
                <img src={preview} alt="Preview" className="w-full h-56 object-cover" />
                <button
                  onClick={handleReset}
                  className="absolute top-3 right-3 p-2 bg-white/90 backdrop-blur-sm rounded-xl shadow-soft hover:bg-white transition-colors"
                >
                  <X size={16} className="text-coffee-700" />
                </button>
              </div>
            )}

            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={(e) => handleFile(e.target.files?.[0])}
              className="hidden"
            />

            {/* Berat Sampel */}
            <div>
              <label className="label">Berat Sampel (gram)</label>
              <div className="relative">
                <input
                  type="number"
                  value={weight}
                  onChange={(e) => setWeight(Number(e.target.value) || 0)}
                  className="input pr-16"
                  min="1" max="10000"
                  placeholder="contoh: 350"
                />
                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-sm text-coffee-400 font-medium">gram</span>
              </div>
              <div className="flex gap-2 mt-2">
                {WEIGHT_PRESETS.map(preset => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => setWeight(preset)}
                    className={`text-xs px-3 py-1 rounded-lg border transition-colors
                      ${weight === preset
                        ? 'bg-bean-600 text-white border-bean-600'
                        : 'bg-white text-coffee-600 border-coffee-200 hover:bg-bean-50'}`}
                  >
                    {preset}g
                  </button>
                ))}
              </div>
              <p className="text-xs text-coffee-400 mt-1.5">Standar SCA: 350g per sampel</p>
            </div>

            {/* Tombol Aksi */}
            <div className="flex gap-3">
              <button
                onClick={handleSubmit}
                disabled={loading || !image}
                className="btn-primary flex-1"
              >
                {loading ? (
                  <><Loader2 size={16} className="animate-spin" /> Menganalisa...</>
                ) : (
                  <><CheckCircle2 size={16} /> Analisa</>
                )}
              </button>
              {preview && !loading && (
                <button onClick={handleReset} className="btn-secondary">
                  <RefreshCw size={16} />
                </button>
              )}
            </div>
          </div>

          {/* Kamera */}
          {/* <div className="card p-5 space-y-4">
            <h3 className="font-semibold text-coffee-800 flex items-center gap-2">
              <Camera size={18} className="text-bean-600" />
              Kamera Langsung
            </h3>
            {!cameraActive ? (
              <button onClick={startCamera} className="btn-secondary w-full">
                <Camera size={16} /> Buka Kamera
              </button>
            ) : (
              <>
                <div className="relative rounded-xl overflow-hidden bg-black">
                  <video ref={videoRef} autoPlay playsInline className="w-full h-48 object-cover" />
                  <button
                    onClick={stopCamera}
                    className="absolute top-2 right-2 p-2 bg-slate-800/70 rounded-lg hover:bg-slate-800 transition"
                  >
                    <CameraOff size={14} className="text-white" />
                  </button>
                </div>
                <button onClick={captureSnapshot} className="btn-primary w-full">
                  Ambil Gambar untuk Analisa
                </button>
              </>
            )}
          </div> */}

          {/* Error */}
          {error && (
            <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-xl animate-slide-down">
              <AlertTriangle size={18} className="text-red-500 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}
        </div>

        {/* Result Section */}
        <div className="lg:col-span-3">
          {loading && (
            <div className="card p-8 text-center animate-fade-in">
              <Loader2 size={36} className="text-bean-600 animate-spin mx-auto mb-4" />
              <p className="font-semibold text-coffee-800">Mendeteksi defect...</p>
              <p className="text-sm text-coffee-400 mt-1">Mohon tunggu sebentar</p>
            </div>
          )}

          {!loading && !result && !error && (
            <div className="card p-8 text-center animate-fade-in min-h-[300px] flex flex-col justify-center items-center">
              <Info size={28} className="text-coffee-300 mb-3" />
              <p className="text-coffee-500 font-medium">Hasil analisa akan tampil di sini</p>
              <p className="text-sm text-coffee-400">Upload gambar dan klik Analisa</p>
            </div>
          )}

          {result && (
            <div className="space-y-5 animate-slide-up">
              {/* Grade & Harga */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="card p-5 flex items-center gap-4">
                  <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold"
                    style={{ backgroundColor: result.grade_color || GRADE_COLORS[result.grade_code] || '#808080' }}
                  >
                    {result.grade_code?.replace('GRADE_', '')}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-coffee-900">{result.grade_name}</p>
                    <p className="text-xs text-coffee-500">{result.grade_code}</p>
                  </div>
                </div>
                <div className="card p-5 text-right">
                  <p className="text-xs text-coffee-500">Estimasi Harga Total</p>
                  <p className="text-2xl font-bold text-coffee-900 font-display">{formatRupiah(result.total_price)}</p>
                  <p className="text-xs text-coffee-400">{formatRupiah(result.price_per_gram)} / gram</p>
                </div>
              </div>

              {/* Statistik */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { label: 'Total Defect', value: result.total_defects, unit: 'item' },
                  { label: 'per 350g', value: result.defects_per_350g?.toFixed(1), unit: 'defect' },
                  { label: 'Confidence', value: (result.confidence_avg * 100)?.toFixed(1), unit: '%' },
                  { label: 'Waktu Proses', value: (result.processing_time_ms / 1000)?.toFixed(2), unit: 'detik' },
                ].map((stat, i) => (
                  <div key={i} className="card p-4 text-center">
                    <p className="text-xs text-coffee-500 mb-1">{stat.label}</p>
                    <p className="text-xl font-bold text-coffee-900 font-display">{stat.value}</p>
                    <p className="text-xs text-coffee-400">{stat.unit}</p>
                  </div>
                ))}
              </div>

              {/* Ringkasan Defect dengan filter kelas */}
              <div className="card p-5">
                <h4 className="text-sm font-semibold text-coffee-800 mb-3">Ringkasan Defect</h4>
                {detectedClasses.length > 0 ? (
                  <>
                    <div className="flex flex-wrap gap-2 mb-2">
                      {detectedClasses.map((name, idx) => {
                        const isActive = activeFilterClass === name
                        return (
                          <button
                            key={name}
                            onClick={() => setActiveFilterClass(isActive ? null : name)}
                            className={`badge text-white px-3 py-1 cursor-pointer transition-all
                              ${isActive ? 'ring-2 ring-offset-1 ring-coffee-700 scale-105' : ''}`}
                            style={{ backgroundColor: DEFECT_COLORS[idx % DEFECT_COLORS.length] }}
                          >
                            {name.replace(/_/g, ' ')} <span className="ml-1 font-bold">{summary[name]}</span>
                          </button>
                        )
                      })}
                    </div>
                    <p className="text-xs text-coffee-500">
                      {activeFilterClass
                        ? `Menampilkan ${summary[activeFilterClass]} deteksi ${activeFilterClass.replace(/_/g, ' ')}`
                        : `Terdeteksi ${detectedClasses.length} kelas cacat dari ${detections.length} objek.`
                      }
                    </p>
                  </>
                ) : (
                  <div className="flex items-center gap-3 text-bean-600">
                    <CheckCircle2 size={20} />
                    <span className="text-sm font-medium">Tidak ada defect terdeteksi.</span>
                  </div>
                )}
              </div>

              {/* Gambar Hasil Deteksi dengan Overlay & Filter */}
              <div className="card overflow-hidden">
                <div className="px-5 py-3 border-b border-coffee-100 flex items-center justify-between">
                  <h4 className="text-sm font-semibold text-coffee-800">Hasil Deteksi Visual</h4>
                  <div className="flex items-center gap-3">
                    {hasDetections && (
                      <label className="flex items-center gap-2 cursor-pointer select-none">
                        <div className="relative">
                          <input
                            type="checkbox"
                            checked={showOverlay}
                            onChange={(e) => setShowOverlay(e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-9 h-5 bg-coffee-200 peer-checked:bg-bean-500 rounded-full transition-colors duration-200 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-4"></div>
                        </div>
                        <span className="text-xs text-coffee-600 flex items-center gap-1">
                          {showOverlay ? <Eye size={14} /> : <EyeOff size={14} />}
                          Box
                        </span>
                      </label>
                    )}
                    <a href={result.result_image_url} download className="btn-ghost text-xs">
                      <Download size={14} /> Unduh Anotasi
                    </a>
                  </div>
                </div>

                <div className="relative" ref={imageContainerRef}>
                  <img
                    ref={mainImageRef}
                    src={preview}
                    alt="Preview"
                    className="w-full"
                    onLoad={handleImageLoad}
                  />
                  {showOverlay && filteredDetections.length > 0 && imageScale.x > 0 && (
                    <div className="absolute inset-0">
                      {filteredDetections.map((det, idx) => {
                        const [x1, y1, x2, y2] = det.bbox
                        const width = (x2 - x1) * imageScale.x
                        const height = (y2 - y1) * imageScale.y
                        const left = x1 * imageScale.x
                        const top = y1 * imageScale.y
                        return (
                          <div
                            key={idx}
                            className={`absolute border-2 transition-all duration-150 cursor-pointer
                              ${highlightedIndex === idx ? 'border-red-500 bg-red-400/20 z-10' : 'border-green-400 bg-green-300/10 hover:bg-green-300/30'}`}
                            style={{ left, top, width, height }}
                            onMouseEnter={() => setHighlightedIndex(idx)}
                            onMouseLeave={() => setHighlightedIndex(null)}
                          >
                            {highlightedIndex === idx && (
                              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-0.5 bg-slate-800 text-white text-[10px] rounded whitespace-nowrap z-20">
                                {det.class_name.replace(/_/g, ' ')} ({(det.confidence * 100).toFixed(1)}%)
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              </div>

              {/* Daftar Deteksi */}
              {filteredDetections.length > 0 && (
                <div className="card overflow-hidden">
                  <button
                    onClick={() => setShowDetectionList(!showDetectionList)}
                    className="w-full px-5 py-3 flex items-center justify-between hover:bg-coffee-50 transition-colors"
                  >
                    <h4 className="text-sm font-semibold text-coffee-800">
                      Daftar Deteksi ({filteredDetections.length})
                    </h4>
                    {showDetectionList ? <ChevronUp size={16} className="text-coffee-400" /> : <ChevronDown size={16} className="text-coffee-400" />}
                  </button>
                  {showDetectionList && (
                    <div className="overflow-x-auto animate-slide-down">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="bg-coffee-50/70 border-y border-coffee-100">
                            <th className="px-4 py-2 text-left text-xs font-semibold text-coffee-500 uppercase">#</th>
                            <th className="px-4 py-2 text-left text-xs font-semibold text-coffee-500 uppercase">Jenis Cacat</th>
                            <th className="px-4 py-2 text-center text-xs font-semibold text-coffee-500 uppercase">Confidence</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredDetections.map((det, idx) => (
                            <tr
                              key={idx}
                              className={`border-b border-coffee-50 transition-colors cursor-pointer
                                ${highlightedIndex === idx ? 'bg-yellow-50' : 'hover:bg-coffee-50/30'}`}
                              onMouseEnter={() => setHighlightedIndex(idx)}
                              onMouseLeave={() => setHighlightedIndex(null)}
                            >
                              <td className="px-4 py-2 text-coffee-400 font-mono">{idx + 1}</td>
                              <td className="px-4 py-2 text-coffee-700 capitalize">{det.class_name.replace(/_/g, ' ')}</td>
                              <td className="px-4 py-2 text-center">
                                <span className="font-mono text-coffee-600">{det.confidence ? (det.confidence * 100).toFixed(1) : '0'}%</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
import { useState, useCallback } from 'react'
import axios from 'axios'
import { useDropzone } from 'react-dropzone'
import {
  Upload as UploadIcon, FileText, CheckCircle2, XCircle,
  Loader2, File, AlertTriangle, CloudUpload, Zap
} from 'lucide-react'

const FILE_ICONS = {
  pdf:  { icon: FileText, color: 'text-red-400',    bg: 'bg-red-500/10' },
  xlsx: { icon: FileText, color: 'text-green-400',  bg: 'bg-green-500/10' },
  xls:  { icon: FileText, color: 'text-green-400',  bg: 'bg-green-500/10' },
  docx: { icon: FileText, color: 'text-brand-400',  bg: 'bg-brand-500/10' },
  csv:  { icon: FileText, color: 'text-amber-400',  bg: 'bg-amber-500/10' },
  png:  { icon: File,     color: 'text-violet-400', bg: 'bg-violet-500/10' },
  jpg:  { icon: File,     color: 'text-violet-400', bg: 'bg-violet-500/10' },
  jpeg: { icon: File,     color: 'text-violet-400', bg: 'bg-violet-500/10' },
  txt:  { icon: FileText, color: 'text-surface-400', bg: 'bg-surface-500/10' },
}

const PIPELINE_STEPS = [
  'Parsing document',
  'Running OCR (if needed)',
  'Extracting entities',
  'Building knowledge graph',
  'Generating embeddings',
  'Saving to vector store',
  'Complete',
]

function FileItem({ file, status, progress }) {
  const ext = file.name.split('.').pop()?.toLowerCase()
  const fIcon = FILE_ICONS[ext] || FILE_ICONS.txt
  const Icon = fIcon.icon
  const sizeMB = (file.size / 1024 / 1024).toFixed(2)

  return (
    <div className="flex items-start gap-3 p-3 rounded-xl bg-surface-900/50 border border-surface-800/60 animate-fade-in">
      <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${fIcon.bg}`}>
        <Icon size={16} className={fIcon.color} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-white truncate">{file.name}</div>
        <div className="text-xs text-surface-400 mt-0.5">{sizeMB} MB • {ext?.toUpperCase()}</div>
        {status === 'uploading' && (
          <div className="mt-2">
            <div className="w-full h-1 bg-surface-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-brand-600 to-brand-400 transition-all duration-500 rounded-full"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="text-[10px] text-surface-500 mt-1">{PIPELINE_STEPS[Math.floor(progress / 16)] || 'Processing...'}</div>
          </div>
        )}
        {status === 'processing' && (
          <div className="flex items-center gap-1.5 mt-1.5 text-xs text-amber-400">
            <Loader2 size={11} className="animate-spin" />
            AI pipeline running...
          </div>
        )}
        {status === 'done' && (
          <div className="flex items-center gap-1.5 mt-1.5 text-xs text-emerald-400">
            <CheckCircle2 size={11} />
            Processed & embedded
          </div>
        )}
        {status === 'error' && (
          <div className="flex items-center gap-1.5 mt-1.5 text-xs text-red-400">
            <XCircle size={11} />
            Upload failed
          </div>
        )}
      </div>
      <div className="flex-shrink-0">
        {status === 'uploading' && <Loader2 size={16} className="animate-spin text-brand-400" />}
        {status === 'processing' && <Loader2 size={16} className="animate-spin text-amber-400" />}
        {status === 'done'  && <CheckCircle2 size={16} className="text-emerald-400" />}
        {status === 'error' && <XCircle size={16} className="text-red-400" />}
        {status === 'queued' && <div className="w-4 h-4 rounded-full border-2 border-surface-600" />}
      </div>
    </div>
  )
}

export default function Upload() {
  const [fileQueue, setFileQueue] = useState([]) // [{file, status, progress, docId}]
  const [uploading, setUploading] = useState(false)

  const onDrop = useCallback((accepted) => {
    const newItems = accepted.map(f => ({ file: f, status: 'queued', progress: 0, docId: null }))
    setFileQueue(prev => [...prev, ...newItems])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/csv': ['.csv'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'text/plain': ['.txt'],
    },
    multiple: true,
  })

  const uploadAll = async () => {
    const queued = fileQueue.filter(item => item.status === 'queued')
    if (!queued.length) return

    setUploading(true)

    for (let i = 0; i < queued.length; i++) {
      const item = queued[i]
      const idx = fileQueue.indexOf(item)

      // Mark as uploading
      setFileQueue(prev => prev.map((it, j) =>
        it === item ? { ...it, status: 'uploading', progress: 5 } : it
      ))

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setFileQueue(prev => prev.map(it =>
          it === item && it.status === 'uploading'
            ? { ...it, progress: Math.min(it.progress + 15, 90) }
            : it
        ))
      }, 400)

      try {
        const formData = new FormData()
        formData.append('files', item.file)

        const res = await axios.post('/api/upload/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })

        clearInterval(progressInterval)
        const fileResult = res.data.files?.[0]

        setFileQueue(prev => prev.map(it =>
          it === item ? { ...it, status: 'processing', progress: 100, docId: fileResult?.document_id } : it
        ))

        // Poll status until ready
        if (fileResult?.document_id) {
          pollStatus(fileResult.document_id, item)
        } else {
          setFileQueue(prev => prev.map(it => it === item ? { ...it, status: 'done' } : it))
        }

      } catch (err) {
        clearInterval(progressInterval)
        setFileQueue(prev => prev.map(it => it === item ? { ...it, status: 'error', progress: 0 } : it))
      }
    }
    setUploading(false)
  }

  const pollStatus = async (docId, item) => {
    for (let attempt = 0; attempt < 20; attempt++) {
      await new Promise(r => setTimeout(r, 2000))
      try {
        const res = await axios.get(`/api/documents/${docId}/status`)
        if (res.data.status === 'ready') {
          setFileQueue(prev => prev.map(it => it === item ? { ...it, status: 'done' } : it))
          return
        }
        if (res.data.status === 'failed') {
          setFileQueue(prev => prev.map(it => it === item ? { ...it, status: 'error' } : it))
          return
        }
      } catch {}
    }
    setFileQueue(prev => prev.map(it => it === item ? { ...it, status: 'done' } : it))
  }

  const queuedCount = fileQueue.filter(i => i.status === 'queued').length
  const doneCount = fileQueue.filter(i => i.status === 'done').length
  const totalCount = fileQueue.length

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Upload Documents</h1>
        <p className="text-surface-300 text-sm mt-0.5">
          Upload industrial documents — they will be automatically processed through the AI pipeline
        </p>
      </div>

      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={`relative border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-200 ${
          isDragActive
            ? 'border-brand-500 bg-brand-500/5 scale-[1.01]'
            : 'border-surface-700 hover:border-brand-500/50 hover:bg-surface-900/30'
        }`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-4">
          <div className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-all ${
            isDragActive ? 'bg-brand-500/20 glow-blue' : 'bg-surface-800'
          }`}>
            <CloudUpload size={28} className={isDragActive ? 'text-brand-400' : 'text-surface-400'} />
          </div>
          <div>
            <div className="text-base font-semibold text-white mb-1">
              {isDragActive ? 'Drop files here...' : 'Drag & drop files here'}
            </div>
            <div className="text-sm text-surface-400">or click to browse</div>
          </div>
          <div className="flex flex-wrap justify-center gap-2 mt-2">
            {['PDF', 'Excel', 'Word', 'CSV', 'Images', 'TXT'].map(t => (
              <span key={t} className="badge badge-ok text-[10px] px-2">{t}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Pipeline Explainer */}
      <div className="glass-card p-4">
        <div className="flex items-center gap-2 mb-3">
          <Zap size={14} className="text-amber-400" />
          <span className="text-xs font-semibold text-white">AI Processing Pipeline</span>
        </div>
        <div className="flex items-center gap-1 flex-wrap">
          {['Upload', 'OCR', 'Extract Entities', 'Build KG', 'Embed', 'Index'].map((step, i, arr) => (
            <div key={step} className="flex items-center gap-1">
              <span className="text-[10px] px-2 py-1 rounded-full bg-surface-800 text-surface-300 border border-surface-700">{step}</span>
              {i < arr.length - 1 && <span className="text-surface-600 text-[10px]">→</span>}
            </div>
          ))}
        </div>
      </div>

      {/* File Queue */}
      {fileQueue.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-sm font-medium text-white">
              Files ({doneCount}/{totalCount} complete)
            </div>
            <div className="flex gap-2">
              <button onClick={() => setFileQueue([])} className="btn-secondary text-xs py-1">
                Clear All
              </button>
              {queuedCount > 0 && (
                <button onClick={uploadAll} disabled={uploading} className="btn-primary text-xs py-1">
                  {uploading ? <Loader2 size={13} className="animate-spin" /> : <UploadIcon size={13} />}
                  Upload {queuedCount} file{queuedCount > 1 ? 's' : ''}
                </button>
              )}
            </div>
          </div>
          <div className="space-y-2">
            {fileQueue.map((item, i) => (
              <FileItem key={i} file={item.file} status={item.status} progress={item.progress} />
            ))}
          </div>
        </div>
      )}

      {/* Sample Documents hint */}
      <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20">
        <div className="flex gap-2">
          <AlertTriangle size={14} className="text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-surface-300">
            <span className="font-semibold text-amber-400">Sample data pre-loaded.</span>{' '}
            The system already has 5 industrial documents (Pump Manual, Maintenance History, Inspection Report, 
            Safety SOP, Boiler Incident). You can start chatting immediately or upload your own documents.
          </div>
        </div>
      </div>
    </div>
  )
}

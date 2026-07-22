import { useEffect, useState } from 'react'
import axios from 'axios'
import { FileText, Search, Filter, Trash2, Clock, CheckCircle2, Loader2, AlertCircle, Eye } from 'lucide-react'

const STATUS_MAP = {
  ready:      { label: 'Ready',      cls: 'badge-ok',       icon: CheckCircle2 },
  processing: { label: 'Processing', cls: 'badge-medium',   icon: Loader2 },
  failed:     { label: 'Failed',     cls: 'badge-critical', icon: AlertCircle },
}

const TYPE_COLORS = {
  pdf:  'text-red-400 bg-red-500/10',
  xlsx: 'text-green-400 bg-green-500/10',
  xls:  'text-green-400 bg-green-500/10',
  docx: 'text-brand-400 bg-brand-500/10',
  csv:  'text-amber-400 bg-amber-500/10',
  txt:  'text-surface-400 bg-surface-500/10',
  png:  'text-violet-400 bg-violet-500/10',
  jpg:  'text-violet-400 bg-violet-500/10',
}

export default function Documents() {
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [selected, setSelected] = useState(null)

  const fetchDocs = () => {
    setLoading(true)
    const params = {}
    if (filterStatus) params.status = filterStatus
    axios.get('/api/documents/', { params })
      .then(r => setDocs(r.data.documents || []))
      .catch(() => setDocs([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchDocs() }, [filterStatus])

  const deleteDoc = async (id) => {
    if (!confirm('Delete this document?')) return
    await axios.delete(`/api/documents/${id}`)
    setDocs(prev => prev.filter(d => d.id !== id))
    if (selected?.id === id) setSelected(null)
  }

  const openDetail = async (doc) => {
    const res = await axios.get(`/api/documents/${doc.id}`)
    setSelected(res.data)
  }

  const filtered = docs.filter(d =>
    d.filename?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="flex h-full">
      {/* Document List */}
      <div className="flex-1 p-6 space-y-4 overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Document Library</h1>
            <p className="text-surface-300 text-sm mt-0.5">{docs.length} documents in knowledge base</p>
          </div>
          <button onClick={fetchDocs} className="btn-secondary text-xs">
            Refresh
          </button>
        </div>

        {/* Filters */}
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-surface-500" />
            <input
              className="input-field pl-9"
              placeholder="Search documents..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <select
            className="input-field w-40"
            value={filterStatus}
            onChange={e => setFilterStatus(e.target.value)}
          >
            <option value="">All Status</option>
            <option value="ready">Ready</option>
            <option value="processing">Processing</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        {/* Table */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 size={24} className="animate-spin text-brand-400" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20">
            <FileText size={40} className="mx-auto text-surface-600 mb-3" />
            <div className="text-surface-400 text-sm">No documents found</div>
            <a href="/upload" className="btn-primary mt-4 inline-flex">Upload Documents</a>
          </div>
        ) : (
          <div className="space-y-2">
            {filtered.map(doc => {
              const ext = doc.file_type || doc.filename?.split('.').pop() || 'txt'
              const typeColor = TYPE_COLORS[ext] || TYPE_COLORS.txt
              const status = STATUS_MAP[doc.status] || STATUS_MAP.ready
              const StatusIcon = status.icon
              const sizeMB = doc.file_size ? (doc.file_size / 1024 / 1024).toFixed(2) : '—'

              return (
                <div
                  key={doc.id}
                  onClick={() => openDetail(doc)}
                  className={`glass-card p-4 flex items-center gap-4 cursor-pointer transition-all
                    ${selected?.id === doc.id ? 'border-brand-500/50 bg-brand-500/5' : ''}`}
                >
                  {/* Type badge */}
                  <div className={`px-2 py-1 rounded-lg text-[10px] font-bold uppercase flex-shrink-0 ${typeColor}`}>
                    {ext}
                  </div>
                  {/* Name */}
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-white truncate">{doc.filename}</div>
                    <div className="text-[11px] text-surface-400 mt-0.5">
                      {sizeMB} MB • {doc.page_count ?? 0} pages • {doc.chunk_count ?? 0} chunks
                    </div>
                    {doc.summary && (
                      <div className="text-[11px] text-surface-500 mt-1 truncate">{doc.summary}</div>
                    )}
                  </div>
                  {/* Date */}
                  <div className="hidden lg:flex items-center gap-1 text-[11px] text-surface-500 flex-shrink-0">
                    <Clock size={10} />
                    {doc.upload_date ? new Date(doc.upload_date).toLocaleDateString() : '—'}
                  </div>
                  {/* Status */}
                  <span className={`badge ${status.cls} flex-shrink-0 flex items-center gap-1`}>
                    <StatusIcon size={9} className={doc.status === 'processing' ? 'animate-spin' : ''} />
                    {status.label}
                  </span>
                  {/* Actions */}
                  <div className="flex gap-1 flex-shrink-0" onClick={e => e.stopPropagation()}>
                    <button onClick={() => openDetail(doc)} className="p-1.5 rounded-lg hover:bg-surface-700 text-surface-400 hover:text-white transition-all">
                      <Eye size={13} />
                    </button>
                    <button onClick={() => deleteDoc(doc.id)} className="p-1.5 rounded-lg hover:bg-red-500/15 text-surface-400 hover:text-red-400 transition-all">
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Detail Panel */}
      {selected && (
        <div className="w-80 flex-shrink-0 border-l border-surface-800 glass p-5 overflow-y-auto animate-fade-in">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-semibold text-white">Document Details</span>
            <button onClick={() => setSelected(null)} className="text-surface-500 hover:text-white text-lg">×</button>
          </div>
          <div className="space-y-4">
            <div>
              <div className="label mb-1">Filename</div>
              <div className="text-sm text-white break-words">{selected.filename}</div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="label mb-1">Pages</div>
                <div className="text-sm text-white">{selected.page_count ?? 0}</div>
              </div>
              <div>
                <div className="label mb-1">Chunks</div>
                <div className="text-sm text-white">{selected.chunk_count ?? 0}</div>
              </div>
            </div>
            {selected.summary && (
              <div>
                <div className="label mb-1">AI Summary</div>
                <div className="text-xs text-surface-300 leading-relaxed">{selected.summary}</div>
              </div>
            )}
            {selected.entities?.length > 0 && (
              <div>
                <div className="label mb-2">Extracted Entities</div>
                <div className="flex flex-wrap gap-1.5">
                  {selected.entities.slice(0, 15).map((e, i) => (
                    <span key={i} className={`badge text-[10px] ${
                      e.type === 'equipment' ? 'badge-ok' :
                      e.type === 'operator' ? 'badge-low' :
                      e.type === 'failure_mode' ? 'badge-critical' : 'badge-medium'
                    }`}>
                      {e.value}
                    </span>
                  ))}
                </div>
              </div>
            )}
            <div>
              <div className="label mb-1">Processed</div>
              <div className="text-xs text-surface-300">
                {selected.processed_date ? new Date(selected.processed_date).toLocaleString() : 'Pending'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

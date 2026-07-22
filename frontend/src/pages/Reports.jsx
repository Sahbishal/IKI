import { useState, useEffect } from 'react'
import axios from 'axios'
import { FileText, Download, Activity, Clock } from 'lucide-react'

export default function Reports() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    fetchReports()
  }, [])

  const fetchReports = async () => {
    try {
      const res = await axios.get('/api/reports')
      setReports(res.data.reports || [])
    } catch (error) {
      console.error('Failed to fetch reports', error)
    } finally {
      setLoading(false)
    }
  }

  const generateReport = async (type) => {
    setGenerating(true)
    try {
      await axios.post('/api/reports/generate', { report_type: type })
      fetchReports()
    } catch (error) {
      console.error('Failed to generate report', error)
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Audit Reports</h1>
          <p className="text-surface-300 text-sm mt-0.5">Generate and download compliance and operational reports</p>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={() => generateReport('monthly')}
            disabled={generating}
            className="btn-primary"
          >
            <Activity size={16} /> {generating ? 'Generating...' : 'Generate Monthly Report'}
          </button>
        </div>
      </div>

      <div className="glass-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <FileText size={16} className="text-brand-400" />
          <span className="section-title text-base">Available Reports</span>
        </div>
        
        {loading ? (
          <div className="text-center py-8 text-surface-400 text-sm">Loading reports...</div>
        ) : reports.length === 0 ? (
          <div className="text-center py-8 text-surface-400 text-sm">
            No reports generated yet. Click "Generate Monthly Report" to create one.
          </div>
        ) : (
          <div className="space-y-3">
            {reports.map((report, idx) => (
              <div key={idx} className="flex items-center justify-between p-4 rounded-lg bg-surface-900/40 border border-surface-800/50 hover:border-surface-700/50 transition-all">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-emerald-500/15 text-emerald-400 flex items-center justify-center">
                    <FileText size={20} />
                  </div>
                  <div>
                    <div className="font-medium text-surface-100">{report.filename || 'Audit Report'}</div>
                    <div className="text-xs text-surface-400 flex items-center gap-1 mt-1">
                      <Clock size={12} /> Generated {new Date(report.generated_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
                <a 
                  href={`/api/reports/download/${report.filename}`}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-secondary"
                >
                  <Download size={14} /> Download PDF
                </a>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

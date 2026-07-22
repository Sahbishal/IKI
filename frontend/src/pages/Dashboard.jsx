import { useEffect, useState } from 'react'
import axios from 'axios'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend,
  ArcElement, PointElement, LineElement, Filler
} from 'chart.js'
import { Bar, Doughnut } from 'react-chartjs-2'
import KPICard from '../components/KPICard'
import {
  FileText, Settings, AlertTriangle, CheckCircle2, ShieldCheck,
  Network, Activity, Layers, Clock, Cpu, TrendingUp, BarChart3
} from 'lucide-react'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement, PointElement, LineElement, Filler)

const chartDefaults = {
  color: '#94a3b8',
  font: { family: 'Inter' },
}
ChartJS.defaults.color = chartDefaults.color
ChartJS.defaults.font.family = chartDefaults.font.family

const RISK_COLORS = {
  Low: '#10b981', Medium: '#f59e0b', High: '#f97316', Critical: '#ef4444'
}

const statusMap = {
  document: { color: 'text-brand-400',   bg: 'bg-brand-500/10', label: 'Doc' },
  maintenance: { color: 'text-amber-400', bg: 'bg-amber-500/10', label: 'Maint' },
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get('/api/dashboard/stats')
      .then(r => setStats(r.data))
      .catch(() => setStats(null))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-full">
      <div className="flex flex-col items-center gap-4">
        <Cpu size={40} className="text-brand-400 animate-spin-slow" />
        <div className="text-surface-300 text-sm">Loading dashboard...</div>
      </div>
    </div>
  )

  const s = stats || {}
  const riskDist = s.risk_distribution || { Low: 0, Medium: 0, High: 0, Critical: 0 }
  const monthlyTrend = s.monthly_maintenance_trend || []

  const doughnutData = {
    labels: Object.keys(riskDist),
    datasets: [{
      data: Object.values(riskDist),
      backgroundColor: Object.keys(riskDist).map(k => RISK_COLORS[k] + '99'),
      borderColor: Object.keys(riskDist).map(k => RISK_COLORS[k]),
      borderWidth: 2,
    }]
  }

  const barData = {
    labels: monthlyTrend.map(m => m.month),
    datasets: [{
      label: 'Maintenance Events',
      data: monthlyTrend.map(m => m.count),
      backgroundColor: 'rgba(59, 130, 246, 0.3)',
      borderColor: '#3b82f6',
      borderWidth: 2,
      borderRadius: 6,
    }]
  }

  const chartOpts = (title) => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      title: { display: false },
      tooltip: {
        backgroundColor: '#1e293b',
        borderColor: '#334155',
        borderWidth: 1,
        titleColor: '#f1f5f9',
        bodyColor: '#94a3b8',
      }
    },
    scales: {
      x: { grid: { color: 'rgba(51,65,85,0.3)' }, ticks: { color: '#64748b' } },
      y: { grid: { color: 'rgba(51,65,85,0.3)' }, ticks: { color: '#64748b' } },
    }
  })

  const overallRisk = s.overall_risk || 'Low'
  const riskBadgeMap = { Low: 'badge-low', Medium: 'badge-medium', High: 'badge-high', Critical: 'badge-critical' }

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Operations Dashboard</h1>
          <p className="text-surface-300 text-sm mt-0.5">Industrial Knowledge Intelligence — Real-time overview</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={riskBadgeMap[overallRisk] || 'badge-low'}>
            Overall Risk: {overallRisk}
          </span>
          <button
            onClick={() => window.location.reload()}
            className="btn-secondary text-xs"
          >
            <Activity size={13} /> Refresh
          </button>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <KPICard icon={FileText}      label="Total Documents"     value={s.total_documents ?? 0}       subtitle={`${s.ready_documents ?? 0} processed`}       color="blue" />
        <KPICard icon={Settings}      label="Equipment Monitored" value={s.total_equipment ?? 0}        subtitle="Across all sections"                           color="purple" />
        <KPICard icon={Clock}         label="Pending Maintenance" value={s.pending_maintenance ?? 0}    subtitle="Awaiting action"                               color="amber" />
        <KPICard icon={ShieldCheck}   label="Compliance Score"    value={`${s.compliance_score ?? 0}%`} subtitle="Safety & regulatory"                           color="green" />
      </div>

      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <KPICard icon={AlertTriangle} label="Critical Equipment"  value={s.critical_equipment ?? 0}     subtitle="Needs immediate attention"                     color="red" />
        <KPICard icon={Activity}      label="Total Maintenance"   value={s.total_maintenance_events ?? 0} subtitle="Historical records"                          color="cyan" />
        <KPICard icon={Network}       label="KG Nodes"            value={s.knowledge_graph?.nodes ?? 0}  subtitle={`${s.knowledge_graph?.edges ?? 0} relations`} color="purple" />
        <KPICard icon={Layers}        label="Vector Chunks"       value={s.vector_chunks ?? 0}           subtitle="Embedded text segments"                       color="blue" />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-3 gap-6">
        {/* Bar Chart */}
        <div className="col-span-2 glass-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 size={16} className="text-brand-400" />
            <span className="section-title text-base">Maintenance Events (6 months)</span>
          </div>
          <div className="h-52">
            <Bar data={barData} options={chartOpts('Maintenance')} />
          </div>
        </div>

        {/* Doughnut */}
        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={16} className="text-brand-400" />
            <span className="section-title text-base">Risk Distribution</span>
          </div>
          <div className="h-36 flex items-center justify-center">
            <Doughnut
              data={doughnutData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                  legend: {
                    position: 'bottom',
                    labels: { color: '#94a3b8', boxWidth: 10, padding: 10, font: { size: 11 } }
                  },
                  tooltip: { backgroundColor: '#1e293b', borderColor: '#334155', borderWidth: 1 }
                }
              }}
            />
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="glass-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <Activity size={16} className="text-brand-400" />
          <span className="section-title text-base">Recent Activity</span>
        </div>
        <div className="space-y-2">
          {(s.recent_activity || []).length === 0 ? (
            <div className="text-surface-400 text-sm py-4 text-center">
              No activity yet — upload documents to get started
            </div>
          ) : (
            (s.recent_activity || []).map((item, i) => (
              <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-surface-900/40 border border-surface-800/50 hover:border-surface-700/50 transition-all">
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center text-[10px] font-bold flex-shrink-0 ${
                  item.type === 'document' ? 'bg-brand-500/15 text-brand-400' : 'bg-amber-500/15 text-amber-400'
                }`}>
                  {item.type === 'document' ? 'D' : 'M'}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-surface-200 truncate">{item.description}</div>
                  {item.timestamp && (
                    <div className="text-[10px] text-surface-500">{new Date(item.timestamp).toLocaleString()}</div>
                  )}
                </div>
                <span className={`badge text-[10px] ${
                  item.status === 'ready' ? 'badge-ok' :
                  item.status === 'processing' ? 'badge-medium' :
                  item.status === 'Critical' ? 'badge-critical' :
                  item.status === 'High' ? 'badge-high' : 'badge-low'
                }`}>{item.status}</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Ask AI Assistant', desc: 'Query your documents', href: '/chat', color: 'from-brand-600/20 to-brand-700/10', border: 'border-brand-500/20', text: 'text-brand-300' },
          { label: 'Upload Documents', desc: 'Add new files for processing', href: '/upload', color: 'from-violet-600/20 to-violet-700/10', border: 'border-violet-500/20', text: 'text-violet-300' },
          { label: 'Generate Report', desc: 'Create audit PDF report', href: '/reports', color: 'from-emerald-600/20 to-emerald-700/10', border: 'border-emerald-500/20', text: 'text-emerald-300' },
        ].map(({ label, desc, href, color, border, text }) => (
          <a key={href} href={href}
            className={`glass-card p-4 bg-gradient-to-br ${color} border ${border} cursor-pointer group transition-all`}>
            <div className={`font-semibold text-sm ${text} group-hover:underline`}>{label}</div>
            <div className="text-xs text-surface-400 mt-1">{desc}</div>
          </a>
        ))}
      </div>
    </div>
  )
}

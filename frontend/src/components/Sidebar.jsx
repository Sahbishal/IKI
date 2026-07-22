import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, MessageSquare, Upload, FileText,
  Network, ClipboardList, Activity, Cpu, ChevronRight
} from 'lucide-react'

const navItems = [
  { to: '/dashboard',       icon: LayoutDashboard, label: 'Dashboard',        desc: 'KPIs & overview' },
  { to: '/chat',            icon: MessageSquare,   label: 'AI Assistant',     desc: 'Ask anything' },
  { to: '/upload',          icon: Upload,          label: 'Upload Docs',      desc: 'Add documents' },
  { to: '/documents',       icon: FileText,        label: 'Documents',        desc: 'Document library' },
  { to: '/knowledge-graph', icon: Network,         label: 'Knowledge Graph',  desc: 'Entity relations' },
  { to: '/reports',         icon: ClipboardList,   label: 'Reports',          desc: 'Audit & compliance' },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col h-full glass border-r border-surface-800">
      {/* Logo */}
      <div className="px-5 py-6 border-b border-surface-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-lg glow-blue">
            <Cpu size={18} className="text-white" />
          </div>
          <div>
            <div className="text-sm font-bold text-white leading-tight">IKI Platform</div>
            <div className="text-[10px] text-surface-300 leading-tight">Industrial AI Brain</div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        <div className="label px-2 mb-3">Navigation</div>
        {navItems.map(({ to, icon: Icon, label, desc }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${
                isActive
                  ? 'bg-brand-600/20 border border-brand-500/30 text-brand-300'
                  : 'text-surface-300 hover:bg-surface-800/60 hover:text-white border border-transparent'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${
                  isActive
                    ? 'bg-brand-500/20 text-brand-400'
                    : 'bg-surface-800 text-surface-400 group-hover:bg-surface-700 group-hover:text-surface-200'
                }`}>
                  <Icon size={15} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium leading-tight truncate">{label}</div>
                  <div className="text-[10px] text-surface-400 truncate">{desc}</div>
                </div>
                {isActive && <ChevronRight size={12} className="text-brand-400 flex-shrink-0" />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Status indicator */}
      <div className="px-4 py-4 border-t border-surface-800">
        <div className="glass-card p-3 rounded-lg">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-slow" />
            <span className="text-xs font-medium text-emerald-400">AI Systems Online</span>
          </div>
          <div className="text-[10px] text-surface-400">Gemini 2.0 Flash • ChromaDB • NetworkX</div>
        </div>
      </div>
    </aside>
  )
}

import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

const riskColorMap = {
  Low:      'text-emerald-400',
  Medium:   'text-amber-400',
  High:     'text-orange-400',
  Critical: 'text-red-400',
}

export default function KPICard({ icon: Icon, label, value, subtitle, trend, color = 'blue', size = 'normal' }) {
  const colorMap = {
    blue:   { icon: 'from-brand-500 to-brand-700',   glow: 'shadow-brand-900/30',   ring: 'border-brand-500/20' },
    green:  { icon: 'from-emerald-500 to-emerald-700', glow: 'shadow-emerald-900/30', ring: 'border-emerald-500/20' },
    amber:  { icon: 'from-amber-500 to-amber-700',   glow: 'shadow-amber-900/30',   ring: 'border-amber-500/20' },
    red:    { icon: 'from-red-500 to-red-700',       glow: 'shadow-red-900/30',     ring: 'border-red-500/20' },
    purple: { icon: 'from-violet-500 to-violet-700', glow: 'shadow-violet-900/30',  ring: 'border-violet-500/20' },
    cyan:   { icon: 'from-cyan-500 to-cyan-700',     glow: 'shadow-cyan-900/30',    ring: 'border-cyan-500/20' },
  }
  const c = colorMap[color] || colorMap.blue

  return (
    <div className={`glass-card p-5 flex items-start gap-4 border ${c.ring}`}>
      {Icon && (
        <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${c.icon} flex items-center justify-center flex-shrink-0 shadow-lg ${c.glow}`}>
          <Icon size={20} className="text-white" />
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="label mb-1">{label}</div>
        <div className={`font-bold text-white leading-none ${size === 'large' ? 'text-4xl' : 'text-2xl'}`}>
          {value ?? '—'}
        </div>
        {subtitle && (
          <div className="text-xs text-surface-300 mt-1 truncate">{subtitle}</div>
        )}
        {trend != null && (
          <div className={`flex items-center gap-1 mt-1 text-xs font-medium ${
            trend > 0 ? 'text-emerald-400' : trend < 0 ? 'text-red-400' : 'text-surface-400'
          }`}>
            {trend > 0 ? <TrendingUp size={11} /> : trend < 0 ? <TrendingDown size={11} /> : <Minus size={11} />}
            {Math.abs(trend)}% vs last month
          </div>
        )}
      </div>
    </div>
  )
}

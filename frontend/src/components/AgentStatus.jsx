import { CheckCircle2, Loader2, Database, Network, Sparkles } from 'lucide-react'

const stepIcons = {
  'Vector Search':           Database,
  'Knowledge Graph Lookup':  Network,
  'LLM Generation':          Sparkles,
  'Equipment ID Detection':  CheckCircle2,
  'Maintenance DB Query':    Database,
  'MTBF Analysis':           CheckCircle2,
  'AI Analysis':             Sparkles,
  'SOP Retrieval':           Database,
  'Inspection Retrieval':    Database,
  'Gap Analysis':            CheckCircle2,
  'AI Report':               Sparkles,
  'Failure Pattern Analysis':Database,
  'AI Summarization':        Sparkles,
}

export default function AgentStatus({ steps = [], isLoading = false }) {
  if (!steps.length && !isLoading) return null

  return (
    <div className="flex flex-col gap-1.5 my-2">
      {isLoading && !steps.length && (
        <div className="flex items-center gap-2 text-xs text-surface-400">
          <Loader2 size={12} className="animate-spin text-brand-400" />
          <span>AI agents processing your query...</span>
        </div>
      )}
      {steps.map((step, i) => {
        const Icon = stepIcons[step.step] || CheckCircle2
        const isDone = step.status === 'done'
        return (
          <div
            key={i}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs transition-all ${
              isDone
                ? 'bg-surface-800/50 border border-surface-700/50'
                : 'bg-brand-500/10 border border-brand-500/20 step-running'
            }`}
          >
            {isDone
              ? <CheckCircle2 size={11} className="text-emerald-400 flex-shrink-0" />
              : <Loader2 size={11} className="animate-spin text-brand-400 flex-shrink-0" />
            }
            <Icon size={10} className={isDone ? 'text-surface-400' : 'text-brand-400'} />
            <span className={isDone ? 'text-surface-300' : 'text-brand-300 font-medium'}>{step.step}</span>
            {step.detail && (
              <span className="text-surface-500 ml-auto truncate max-w-[160px]">{step.detail}</span>
            )}
          </div>
        )
      })}
    </div>
  )
}

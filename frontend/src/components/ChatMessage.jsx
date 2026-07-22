import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import AgentStatus from './AgentStatus'
import { Bot, User, BookOpen, ExternalLink } from 'lucide-react'

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 animate-fade-in ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
        isUser
          ? 'bg-brand-600'
          : 'bg-gradient-to-br from-violet-600 to-brand-600'
      }`}>
        {isUser ? <User size={15} className="text-white" /> : <Bot size={15} className="text-white" />}
      </div>

      {/* Content */}
      <div className={`flex flex-col gap-2 max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Agent Steps (only for assistant) */}
        {!isUser && message.agent_steps?.length > 0 && (
          <AgentStatus steps={message.agent_steps} />
        )}

        {/* Bubble */}
        <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
          isUser
            ? 'bg-brand-600/30 border border-brand-500/30 text-white rounded-tr-sm'
            : 'bg-surface-800/70 border border-surface-700/50 text-surface-100 rounded-tl-sm'
        }`}>
          {isUser ? (
            <span>{message.content}</span>
          ) : (
            <div className="prose prose-invert prose-sm max-w-none
              prose-headings:text-white prose-headings:font-semibold
              prose-p:text-surface-200 prose-p:leading-relaxed
              prose-strong:text-white prose-strong:font-semibold
              prose-code:text-brand-300 prose-code:bg-surface-900 prose-code:px-1 prose-code:rounded
              prose-pre:bg-surface-900 prose-pre:border prose-pre:border-surface-700
              prose-li:text-surface-200 prose-blockquote:border-brand-500
              prose-table:text-xs prose-th:text-surface-100 prose-td:text-surface-200">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Citations */}
        {!isUser && message.citations?.length > 0 && (
          <div className="flex flex-col gap-1.5 w-full">
            <div className="flex items-center gap-1.5 text-[10px] text-surface-400 font-medium uppercase tracking-wider">
              <BookOpen size={10} />
              Sources
            </div>
            <div className="flex flex-wrap gap-1.5">
              {message.citations.map((c, i) => (
                <div
                  key={i}
                  title={c.excerpt}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface-800/60
                    border border-surface-700/40 text-[11px] text-surface-300 hover:border-brand-500/40
                    hover:text-brand-300 cursor-pointer transition-all group"
                >
                  <BookOpen size={9} className="text-surface-500 group-hover:text-brand-400" />
                  <span className="font-medium truncate max-w-[160px]">{c.document}</span>
                  {c.page && c.page !== '?' && (
                    <span className="text-surface-500">p.{c.page}</span>
                  )}
                  <span className="text-surface-600 text-[9px]">{Math.round(c.relevance_score * 100)}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Timestamp */}
        {message.timestamp && (
          <div className="text-[10px] text-surface-500">
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  )
}

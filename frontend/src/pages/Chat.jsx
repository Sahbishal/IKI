import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import ChatMessage from '../components/ChatMessage'
import AgentStatus from '../components/AgentStatus'
import { Send, Sparkles, Trash2, MessageSquare, Lightbulb, Bot } from 'lucide-react'

const SUGGESTIONS = [
  "Why is Pump P-101 repeatedly failing?",
  "Show all maintenance performed on Compressor C-22",
  "Is Boiler B-5 compliant with safety regulations?",
  "Which equipment has the highest failure rate?",
  "What are the most common failure modes in the plant?",
  "What lessons can we learn from past boiler incidents?",
]

export default function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [showSuggestions, setShowSuggestions] = useState(true)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const sendMessage = async (text) => {
    const msg = (text || input).trim()
    if (!msg || loading) return

    setInput('')
    setShowSuggestions(false)

    const userMessage = { role: 'user', content: msg, timestamp: new Date().toISOString() }
    setMessages(prev => [...prev, userMessage])
    setLoading(true)

    try {
      const res = await axios.post('/api/chat/', {
        message: msg,
        session_id: sessionId,
      })
      const data = res.data
      setSessionId(data.session_id)

      const assistantMessage = {
        role: 'assistant',
        content: data.answer,
        citations: data.citations || [],
        agent_steps: data.agent_steps || [],
        intent: data.intent,
        timestamp: data.timestamp,
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `**Error:** ${err.response?.data?.detail || 'Could not reach the AI backend. Please ensure the server is running.'}`,
        citations: [],
        agent_steps: [],
        timestamp: new Date().toISOString(),
      }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const clearChat = async () => {
    if (sessionId) {
      await axios.delete(`/api/chat/${sessionId}`).catch(() => {})
    }
    setMessages([])
    setSessionId(null)
    setShowSuggestions(true)
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-surface-800 glass flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-600 to-brand-600 flex items-center justify-center">
            <Bot size={18} className="text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white">Industrial AI Assistant</h1>
            <div className="text-[11px] text-surface-400">RAG + Knowledge Graph + Gemini 2.0 Flash</div>
          </div>
        </div>
        {messages.length > 0 && (
          <button onClick={clearChat} className="btn-secondary text-xs">
            <Trash2 size={13} /> New Chat
          </button>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && showSuggestions && (
          <div className="flex flex-col items-center justify-center min-h-[60%] gap-6 animate-slide-up">
            {/* Hero */}
            <div className="text-center max-w-md">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-600 to-brand-600 flex items-center justify-center mx-auto mb-4 glow-blue">
                <Sparkles size={28} className="text-white" />
              </div>
              <h2 className="text-xl font-bold text-white mb-2">Ask Anything About Your Plant</h2>
              <p className="text-surface-300 text-sm leading-relaxed">
                Query equipment history, compliance status, maintenance records, and operational insights — 
                powered by your uploaded documents.
              </p>
            </div>

            {/* Suggestions */}
            <div className="w-full max-w-2xl">
              <div className="flex items-center gap-2 mb-3">
                <Lightbulb size={13} className="text-amber-400" />
                <span className="text-xs font-medium text-surface-400 uppercase tracking-wider">Suggested Questions</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {SUGGESTIONS.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(s)}
                    className="text-left px-4 py-3 rounded-xl glass-card border border-surface-700/40
                      hover:border-brand-500/40 text-sm text-surface-200 hover:text-white
                      transition-all group"
                  >
                    <span className="text-brand-500 mr-2 group-hover:text-brand-400">→</span>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} />
        ))}

        {loading && (
          <div className="flex gap-3 animate-fade-in">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-600 to-brand-600 flex items-center justify-center flex-shrink-0">
              <Bot size={15} className="text-white" />
            </div>
            <div className="flex flex-col gap-2">
              <AgentStatus steps={[]} isLoading={true} />
              <div className="px-4 py-3 rounded-2xl rounded-tl-sm bg-surface-800/70 border border-surface-700/50">
                <div className="flex gap-1">
                  {[0, 1, 2].map(i => (
                    <div key={i} className="w-2 h-2 rounded-full bg-surface-500 animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }} />
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input Bar */}
      <div className="px-6 py-4 border-t border-surface-800 glass flex-shrink-0">
        <div className="flex gap-3 items-end max-w-4xl mx-auto">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask about equipment, failures, compliance, maintenance..."
              rows={1}
              className="w-full px-4 py-3 pr-12 rounded-xl bg-surface-800/80 border border-surface-700
                text-surface-100 placeholder-surface-500 text-sm resize-none
                focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent
                transition-all duration-200 max-h-32"
              style={{ minHeight: '48px' }}
              onInput={e => {
                e.target.style.height = 'auto'
                e.target.style.height = Math.min(e.target.scrollHeight, 128) + 'px'
              }}
            />
            <div className="absolute right-3 bottom-2.5 text-[10px] text-surface-500">Enter ↵</div>
          </div>
          <button
            onClick={() => sendMessage()}
            disabled={!input.trim() || loading}
            className="w-11 h-11 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-40
              disabled:cursor-not-allowed flex items-center justify-center transition-all
              active:scale-95 shadow-lg shadow-brand-900/40 flex-shrink-0"
          >
            <Send size={16} className="text-white" />
          </button>
        </div>
        <div className="text-center text-[10px] text-surface-600 mt-2">
          AI responses are grounded in your uploaded documents. Always verify critical decisions.
        </div>
      </div>
    </div>
  )
}

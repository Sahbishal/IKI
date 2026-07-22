import { useEffect, useState, useCallback } from 'react'
import axios from 'axios'
import ReactFlow, {
  Background, Controls, MiniMap,
  useNodesState, useEdgesState, addEdge,
  MarkerType,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Network, Search, Info, Layers, GitBranch, Loader2 } from 'lucide-react'

const TYPE_COLORS = {
  equipment:        { bg: '#1d4ed8', border: '#3b82f6', text: '#bfdbfe' },
  operator:         { bg: '#065f46', border: '#10b981', text: '#a7f3d0' },
  location:         { bg: '#92400e', border: '#f59e0b', text: '#fde68a' },
  failure_event:    { bg: '#7f1d1d', border: '#ef4444', text: '#fca5a5' },
  maintenance_event:{ bg: '#4c1d95', border: '#8b5cf6', text: '#ddd6fe' },
  inspection_event: { bg: '#164e63', border: '#06b6d4', text: '#a5f3fc' },
  document:         { bg: '#1e293b', border: '#475569', text: '#94a3b8' },
  regulation:       { bg: '#7c2d12', border: '#f97316', text: '#fed7aa' },
  default:          { bg: '#1e293b', border: '#475569', text: '#94a3b8' },
}

function buildFlowElements(graphData) {
  if (!graphData?.nodes) return { nodes: [], edges: [] }

  const nodes = graphData.nodes.map((node, i) => {
    const colors = TYPE_COLORS[node.type] || TYPE_COLORS.default
    return {
      id: node.id,
      type: 'default',
      position: {
        x: 200 + Math.cos((i / graphData.nodes.length) * 2 * Math.PI) * 350,
        y: 300 + Math.sin((i / graphData.nodes.length) * 2 * Math.PI) * 200,
      },
      data: { label: node.label, nodeType: node.type, extra: node.data },
      style: {
        background: colors.bg,
        border: `2px solid ${colors.border}`,
        color: colors.text,
        borderRadius: '10px',
        padding: '8px 14px',
        fontSize: '11px',
        fontFamily: 'Inter',
        fontWeight: 600,
        minWidth: '100px',
        textAlign: 'center',
        boxShadow: `0 0 12px ${colors.border}30`,
        cursor: 'pointer',
      },
    }
  })

  const edges = graphData.edges.map(edge => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    label: edge.label,
    type: 'smoothstep',
    animated: edge.label?.includes('FAILURE') || edge.label?.includes('HAD'),
    style: { stroke: edge.label?.includes('FAILURE') ? '#ef4444' : '#334155', strokeWidth: 1.5 },
    labelStyle: { fill: '#64748b', fontSize: 9, fontFamily: 'Inter' },
    labelBgStyle: { fill: '#0f172a', fillOpacity: 0.8 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#334155', width: 12, height: 12 },
  }))

  return { nodes, edges }
}

export default function KnowledgeGraph() {
  const [graphData, setGraphData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [selected, setSelected] = useState(null)
  const [search, setSearch] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [stats, setStats] = useState({})

  useEffect(() => {
    Promise.all([
      axios.get('/api/graph/'),
      axios.get('/api/graph/stats'),
    ]).then(([graphRes, statsRes]) => {
      const data = graphRes.data
      setGraphData(data)
      const { nodes: n, edges: e } = buildFlowElements(data)
      setNodes(n)
      setEdges(e)
      setStats(statsRes.data)
    }).catch(console.error).finally(() => setLoading(false))
  }, [])

  const onNodeClick = async (_, node) => {
    try {
      const res = await axios.get(`/api/graph/entity/${node.id}`)
      setSelected(res.data)
    } catch {
      setSelected({ entity: { label: node.data.label, type: node.data.nodeType }, connections: [] })
    }
  }

  const handleSearch = async (q) => {
    setSearch(q)
    if (q.length < 2) { setSearchResults([]); return }
    const res = await axios.get(`/api/graph/search?q=${encodeURIComponent(q)}`)
    setSearchResults(res.data.results || [])
  }

  const legendItems = Object.entries(TYPE_COLORS).filter(([k]) => k !== 'default').slice(0, 7)

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-surface-800 glass flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-600 to-brand-600 flex items-center justify-center">
            <Network size={17} className="text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white">Knowledge Graph Explorer</h1>
            <div className="text-[11px] text-surface-400">
              {stats.nodes ?? 0} nodes • {stats.edges ?? 0} relations • {stats.equipment_count ?? 0} equipment
            </div>
          </div>
        </div>
        {/* Search */}
        <div className="relative w-60">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-surface-500" />
          <input
            className="input-field pl-9 py-1.5 text-xs"
            placeholder="Search entities..."
            value={search}
            onChange={e => handleSearch(e.target.value)}
          />
          {searchResults.length > 0 && (
            <div className="absolute top-full mt-1 w-full bg-surface-900 border border-surface-700 rounded-lg shadow-xl z-50 max-h-48 overflow-y-auto">
              {searchResults.map(r => (
                <div key={r.id} className="px-3 py-2 hover:bg-surface-800 cursor-pointer text-xs text-surface-200 transition-all"
                  onClick={async () => {
                    const res = await axios.get(`/api/graph/entity/${r.id}`)
                    setSelected(res.data)
                    setSearch('')
                    setSearchResults([])
                  }}>
                  <span className="font-medium">{r.label || r.id}</span>
                  <span className="text-surface-500 ml-2">{r.type}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Graph Canvas */}
        <div className="flex-1 relative">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="flex flex-col items-center gap-3">
                <Loader2 size={28} className="animate-spin text-brand-400" />
                <div className="text-surface-400 text-sm">Loading knowledge graph...</div>
              </div>
            </div>
          ) : nodes.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-4">
              <Network size={48} className="text-surface-600" />
              <div className="text-center">
                <div className="text-white font-medium mb-1">Knowledge Graph Empty</div>
                <div className="text-surface-400 text-sm">Upload documents to automatically build the graph</div>
              </div>
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={onNodeClick}
              fitView
              fitViewOptions={{ padding: 0.2 }}
              minZoom={0.2}
              maxZoom={2}
            >
              <Background color="#1e293b" gap={20} size={1} />
              <Controls
                style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }}
              />
              <MiniMap
                style={{ background: '#0f172a', border: '1px solid #334155' }}
                nodeColor={(n) => {
                  const c = TYPE_COLORS[n.data?.nodeType] || TYPE_COLORS.default
                  return c.border
                }}
              />
            </ReactFlow>
          )}

          {/* Legend */}
          <div className="absolute bottom-4 left-4 glass rounded-xl p-3 z-10">
            <div className="label mb-2 flex items-center gap-1">
              <Layers size={10} /> Legend
            </div>
            <div className="space-y-1">
              {legendItems.map(([type, colors]) => (
                <div key={type} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-sm flex-shrink-0" style={{ background: colors.border }} />
                  <span className="text-[10px] text-surface-300 capitalize">{type.replace('_', ' ')}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Detail Panel */}
        {selected && (
          <div className="w-72 flex-shrink-0 border-l border-surface-800 glass p-5 overflow-y-auto animate-fade-in">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm font-semibold text-white">Entity Details</span>
              <button onClick={() => setSelected(null)} className="text-surface-500 hover:text-white text-lg">×</button>
            </div>
            {selected.entity && (
              <div className="space-y-4">
                <div>
                  <div className="label mb-1">Label</div>
                  <div className="text-base font-bold text-white">{selected.entity.label || selected.entity.id}</div>
                </div>
                <div>
                  <div className="label mb-1">Type</div>
                  <span className={`badge text-[10px] ${
                    selected.entity.type === 'equipment' ? 'badge-ok' :
                    selected.entity.type === 'failure_event' ? 'badge-critical' :
                    selected.entity.type === 'operator' ? 'badge-low' : 'badge-medium'
                  }`}>
                    {selected.entity.type}
                  </span>
                </div>
                {/* Properties */}
                {Object.entries(selected.entity).filter(([k]) =>
                  !['id', 'label', 'type', 'created_at'].includes(k)
                ).map(([k, v]) => (
                  <div key={k}>
                    <div className="label mb-1">{k.replace(/_/g, ' ')}</div>
                    <div className="text-xs text-surface-300">{String(v)}</div>
                  </div>
                ))}
                {/* Connections */}
                {selected.connections?.length > 0 && (
                  <div>
                    <div className="label mb-2 flex items-center gap-1">
                      <GitBranch size={10} /> Connections ({selected.connections.length})
                    </div>
                    <div className="space-y-1.5">
                      {selected.connections.map((c, i) => (
                        <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-surface-900/50 border border-surface-800/50">
                          <div className="flex-1 min-w-0">
                            <div className="text-xs font-medium text-white truncate">{c.label}</div>
                            <div className="text-[10px] text-surface-500">{c.type}</div>
                          </div>
                          <span className="text-[9px] text-surface-500 font-mono truncate max-w-[80px]">{c.relation}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

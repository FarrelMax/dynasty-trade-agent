import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

const API = 'http://localhost:8000'

function PlayerPanel({ title, players, onAdd, onRemove, accentColor }) {
  const [input, setInput] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [searching, setSearching] = useState(false)

  async function search(val) {
    setInput(val)
    if (val.length < 2) { setSuggestions([]); return }
    setSearching(true)
    try {
      const res = await fetch(`${API}/players/search/${encodeURIComponent(val)}`)
      const data = await res.json()
      setSuggestions(data.slice(0, 5))
    } catch { setSuggestions([]) }
    setSearching(false)
  }

  function pick(player) {
    onAdd(player)
    setInput('')
    setSuggestions([])
  }

  return (
    <div className="card" style={{ flex: 1, minHeight: 320 }}>
      <div style={{
        fontFamily: 'var(--font-display)',
        fontSize: '1.1rem',
        fontWeight: 800,
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        color: accentColor,
        marginBottom: '1rem',
        paddingBottom: '0.75rem',
        borderBottom: `1px solid var(--border)`
      }}>
        {title}
      </div>

      {/* Added players */}
      <div style={{ marginBottom: '1rem', minHeight: 80 }}>
        {players.length === 0 && (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontFamily: 'var(--font-mono)', padding: '0.5rem 0' }}>
            No players added yet
          </div>
        )}
        {players.map((p, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', borderBottom: '1px solid var(--border)' }}>
            <div>
              <span style={{ fontWeight: 500, fontSize: '0.9rem' }}>{p.player_name}</span>
              <span style={{ marginLeft: '0.5rem' }} className="tag tag-pos">{p.position}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              {p.fantasy_value && (
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: accentColor }}>
                  {p.fantasy_value.toLocaleString()}
                </span>
              )}
              <button
                onClick={() => onRemove(i)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1rem', lineHeight: 1 }}
              >×</button>
            </div>
          </div>
        ))}
      </div>

      {/* Search input */}
      <div style={{ position: 'relative' }}>
        <input
          className="search-input"
          style={{ width: '100%' }}
          placeholder="Add player..."
          value={input}
          onChange={e => search(e.target.value)}
        />
        {suggestions.length > 0 && (
          <div style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-bright)',
            borderRadius: 8,
            zIndex: 10,
            marginTop: 4,
            overflow: 'hidden'
          }}>
            {suggestions.map((s, i) => (
              <div
                key={i}
                onClick={() => pick(s)}
                style={{
                  padding: '0.6rem 1rem',
                  cursor: 'pointer',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderBottom: i < suggestions.length - 1 ? '1px solid var(--border)' : 'none',
                  transition: 'background 0.1s'
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                <div>
                  <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>{s.player_name}</span>
                  <span style={{ marginLeft: '0.5rem' }} className="tag tag-pos">{s.position}</span>
                  <span style={{ marginLeft: '0.4rem' }} className="tag tag-team">{s.nfl_team_abb}</span>
                </div>
                {s.fantasy_value && (
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: accentColor }}>
                    {s.fantasy_value.toLocaleString()}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Total */}
      {players.length > 0 && (
        <div style={{ marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Total Value</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1rem', color: accentColor, fontWeight: 600 }}>
            {players.reduce((sum, p) => sum + (p.fantasy_value || 0), 0).toLocaleString()}
          </span>
        </div>
      )}
    </div>
  )
}

export default function TradeEvaluator() {
  const [teamA, setTeamA] = useState([])
  const [teamB, setTeamB] = useState([])
  const [context, setContext] = useState('')
  const [analysis, setAnalysis] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function evaluate() {
    if (teamA.length === 0 || teamB.length === 0) {
      setError('Add at least one player to each side.')
      return
    }
    setLoading(true)
    setError('')
    setAnalysis('')
    try {
      const res = await fetch(`${API}/evaluate-trade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          team_a_gives: teamA.map(p => p.player_name),
          team_b_gives: teamB.map(p => p.player_name),
          context
        })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail)
      setAnalysis(data.analysis)
    } catch (e) {
      setError(e.message || 'Something went wrong.')
    }
    setLoading(false)
  }

  return (
    <div>
      <h1 className="page-title">Trade Evaluator</h1>
      <p className="page-subtitle">Add players to each side and get an AI-powered dynasty analysis</p>

      {/* Two panels */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', alignItems: 'flex-start' }}>
        <PlayerPanel
          title="You Give"
          players={teamA}
          onAdd={p => setTeamA(prev => [...prev, p])}
          onRemove={i => setTeamA(prev => prev.filter((_, idx) => idx !== i))}
          accentColor="#f85149"
        />
        <div style={{ display: 'flex', alignItems: 'center', paddingTop: '5rem', color: 'var(--text-muted)', fontFamily: 'var(--font-display)', fontSize: '1.4rem', fontWeight: 800 }}>
          VS
        </div>
        <PlayerPanel
          title="You Receive"
          players={teamB}
          onAdd={p => setTeamB(prev => [...prev, p])}
          onRemove={i => setTeamB(prev => prev.filter((_, idx) => idx !== i))}
          accentColor="var(--green)"
        />
      </div>

      {/* Context */}
      <div style={{ marginBottom: '1rem' }}>
        <input
          className="search-input"
          style={{ width: '100%' }}
          placeholder="Optional context: e.g. superflex league, I am rebuilding..."
          value={context}
          onChange={e => setContext(e.target.value)}
        />
      </div>

      {error && <div className="error-msg">{error}</div>}

      <button className="btn btn-primary" onClick={evaluate} disabled={loading} style={{ width: '100%', padding: '0.85rem', fontSize: '1.1rem', marginBottom: '1.5rem' }}>
        {loading ? 'Analyzing trade...' : 'Evaluate Trade'}
      </button>

      {/* Analysis output */}
      {loading && (
        <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
          <div className="loading">⚡ Agent is analyzing your trade...</div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.5rem' }}>This usually takes 15–30 seconds</div>
        </div>
      )}

      {analysis && (
        <div className="card" style={{ lineHeight: 1.7 }}>
          <div style={{
            fontFamily: 'var(--font-display)',
            fontSize: '1rem',
            fontWeight: 700,
            letterSpacing: '0.06em',
            color: 'var(--text-secondary)',
            textTransform: 'uppercase',
            marginBottom: '1rem',
            paddingBottom: '0.75rem',
            borderBottom: '1px solid var(--border)'
          }}>
            AI Analysis
          </div>
          <div style={{ fontSize: '0.9rem' }}>
            <ReactMarkdown
              components={{
                h2: ({children}) => <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.3rem', fontWeight: 800, letterSpacing: '0.04em', margin: '1.25rem 0 0.5rem', color: 'var(--text-primary)' }}>{children}</h2>,
                h3: ({children}) => <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.05rem', fontWeight: 700, letterSpacing: '0.04em', margin: '1rem 0 0.4rem', color: 'var(--accent)' }}>{children}</h3>,
                p: ({children}) => <p style={{ marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>{children}</p>,
                strong: ({children}) => <strong style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{children}</strong>,
                li: ({children}) => <li style={{ marginBottom: '0.3rem', color: 'var(--text-secondary)' }}>{children}</li>,
                ul: ({children}) => <ul style={{ paddingLeft: '1.25rem', marginBottom: '0.75rem' }}>{children}</ul>,
                hr: () => <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '1rem 0' }} />,
              }}
            >
              {analysis}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  )
}

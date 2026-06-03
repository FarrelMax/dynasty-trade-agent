import { useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

const API = import.meta.env.VITE_API_URL


export default function PlayerSearch() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [selected, setSelected] = useState(null)
  const [stats, setStats] = useState(null)
  const [history, setHistory] = useState(null)
  const [loading, setLoading] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState('')

  async function search() {
    if (!query.trim()) return
    setLoading(true)
    setError('')
    setSelected(null)
    setStats(null)
    setHistory(null)
    try {
      const res = await fetch(`${API}/players/search/${encodeURIComponent(query)}`)
      const data = await res.json()
      setResults(data)
      if (data.length === 0) setError('No players found.')
    } catch {
      setError('Could not connect to API.')
    }
    setLoading(false)
  }

  async function selectPlayer(player) {
    setSelected(player)
    setDetailLoading(true)
    setStats(null)
    setHistory(null)
    try {
      const [statsRes, historyRes] = await Promise.all([
        fetch(`${API}/players/${encodeURIComponent(player.player_name)}/stats?season=2024`),
        fetch(`${API}/players/${encodeURIComponent(player.player_name)}/value-history`)
      ])
      if (statsRes.ok) setStats(await statsRes.json())
      if (historyRes.ok) setHistory(await historyRes.json())
    } catch {
      // silently fail — player card still shows
    }
    setDetailLoading(false)
  }

  function calcAge(dob) {
    if (!dob) return '—'
    const diff = Date.now() - new Date(dob).getTime()
    return Math.floor(diff / (1000 * 60 * 60 * 24 * 365.25))
  }

  const totalStats = stats?.games?.reduce((acc, g) => ({
    rec: acc.rec + (g.receptions || 0),
    recYds: acc.recYds + (g.receiving_yards || 0),
    recTd: acc.recTd + (g.receiving_touchdowns || 0),
    rushYds: acc.rushYds + (g.rushing_yards || 0),
    rushTd: acc.rushTd + (g.rushing_touchdowns || 0),
    passYds: acc.passYds + (g.passing_yards || 0),
    passTd: acc.passTd + (g.passing_touchdowns || 0),
  }), { rec: 0, recYds: 0, recTd: 0, rushYds: 0, rushTd: 0, passYds: 0, passTd: 0 })

  return (
    <div>
      <h1 className="page-title">Player Search</h1>
      <p className="page-subtitle">Search any NFL player to see their dynasty value and stats</p>

      <div className="search-bar">
        <input
          className="search-input"
          placeholder="Search player name..."
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && search()}
        />
        <button className="btn btn-primary" onClick={search} disabled={loading}>
          {loading ? '...' : 'Search'}
        </button>
      </div>

      {error && <div className="error-msg">{error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: selected ? '280px 1fr' : '1fr', gap: '1.5rem' }}>

        {/* RESULTS LIST */}
        {results.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {results.map((p, i) => (
              <div
                key={i}
                className="card"
                onClick={() => selectPlayer(p)}
                style={{
                  cursor: 'pointer',
                  border: selected?.player_name === p.player_name ? '1px solid var(--accent)' : '1px solid var(--border)',
                  transition: 'all 0.15s ease'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.95rem', marginBottom: '0.35rem' }}>{p.player_name}</div>
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      <span className="tag tag-pos">{p.position}</span>
                      <span className="tag tag-team">{p.nfl_team_abb}</span>
                    </div>
                  </div>
                  {p.fantasy_value && (
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.1rem', color: 'var(--accent)', fontWeight: 600 }}>
                        {p.fantasy_value.toLocaleString()}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>VALUE</div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* PLAYER DETAIL */}
        {selected && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

            {/* Header */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <div>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.8rem', fontWeight: 800, letterSpacing: '0.04em' }}>
                    {selected.player_name}
                  </div>
                  <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.4rem' }}>
                    <span className="tag tag-pos">{selected.position}</span>
                    <span className="tag tag-team">{selected.nfl_team_abb}</span>
                  </div>
                </div>
                {selected.fantasy_value && (
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '2rem', color: 'var(--accent)', fontWeight: 600 }}>
                      {selected.fantasy_value.toLocaleString()}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', letterSpacing: '0.06em' }}>DYNASTY VALUE</div>
                  </div>
                )}
              </div>
            </div>

            {detailLoading && <div className="loading">Loading player data...</div>}

            {/* Stats */}
            {totalStats && (
              <div className="card">
                <div style={{ fontFamily: 'var(--font-display)', fontSize: '1rem', fontWeight: 700, letterSpacing: '0.06em', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '0.75rem' }}>
                  2024 Season Stats
                </div>
                {selected.position === 'QB' ? (
                  <>
                    <div className="stat-row"><span className="stat-label">Passing Yards</span><span className="stat-value">{totalStats.passYds.toLocaleString()}</span></div>
                    <div className="stat-row"><span className="stat-label">Passing TDs</span><span className="stat-value">{totalStats.passTd}</span></div>
                    <div className="stat-row"><span className="stat-label">Rushing Yards</span><span className="stat-value">{totalStats.rushYds.toLocaleString()}</span></div>
                    <div className="stat-row"><span className="stat-label">Games</span><span className="stat-value">{stats.games.length}</span></div>
                  </>
                ) : selected.position === 'RB' ? (
                  <>
                    <div className="stat-row"><span className="stat-label">Rushing Yards</span><span className="stat-value">{totalStats.rushYds.toLocaleString()}</span></div>
                    <div className="stat-row"><span className="stat-label">Rushing TDs</span><span className="stat-value">{totalStats.rushTd}</span></div>
                    <div className="stat-row"><span className="stat-label">Receptions</span><span className="stat-value">{totalStats.rec}</span></div>
                    <div className="stat-row"><span className="stat-label">Receiving Yards</span><span className="stat-value">{totalStats.recYds.toLocaleString()}</span></div>
                    <div className="stat-row"><span className="stat-label">Games</span><span className="stat-value">{stats.games.length}</span></div>
                  </>
                ) : (
                  <>
                    <div className="stat-row"><span className="stat-label">Receptions</span><span className="stat-value">{totalStats.rec}</span></div>
                    <div className="stat-row"><span className="stat-label">Receiving Yards</span><span className="stat-value">{totalStats.recYds.toLocaleString()}</span></div>
                    <div className="stat-row"><span className="stat-label">Receiving TDs</span><span className="stat-value">{totalStats.recTd}</span></div>
                    <div className="stat-row"><span className="stat-label">Games</span><span className="stat-value">{stats.games.length}</span></div>
                  </>
                )}
              </div>
            )}

            {/* Value History Chart */}
            {history?.history?.length > 0 && (
              <div className="card">
                <div style={{ fontFamily: 'var(--font-display)', fontSize: '1rem', fontWeight: 700, letterSpacing: '0.06em', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '1rem' }}>
                  Value History
                </div>
                <ResponsiveContainer width="100%" height={180}>
                  <LineChart data={history.history}>
                    <XAxis dataKey="valuation_date" tick={{ fill: '#484f58', fontSize: 11, fontFamily: 'DM Mono' }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fill: '#484f58', fontSize: 11, fontFamily: 'DM Mono' }} tickLine={false} axisLine={false} domain={['auto', 'auto']} />
                    <Tooltip
                      contentStyle={{ background: '#0d1117', border: '1px solid #21262d', borderRadius: 6, fontFamily: 'DM Mono', fontSize: 12 }}
                      labelStyle={{ color: '#8b949e' }}
                      itemStyle={{ color: '#00e5ff' }}
                    />
                    <Line type="monotone" dataKey="fantasy_value" stroke="#00e5ff" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

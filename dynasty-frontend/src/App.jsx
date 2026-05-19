import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import PlayerSearch from './pages/PlayerSearch'
import TradeEvaluator from './pages/TradeEvaluator'
import './App.css'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="navbar">
          <div className="nav-brand">
            <span className="brand-icon">⚡</span>
            <span className="brand-name">DYNASTY<span className="brand-accent">IQ</span></span>
          </div>
          <div className="nav-links">
            <NavLink to="/" end className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              Player Search
            </NavLink>
            <NavLink to="/trade" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              Trade Evaluator
            </NavLink>
          </div>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<PlayerSearch />} />
            <Route path="/trade" element={<TradeEvaluator />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

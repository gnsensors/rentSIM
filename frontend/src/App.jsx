import { useEffect, useState } from 'react'
import { Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Login from './pages/Login'
import Register from './pages/Register'
import PortfolioCard from './components/PortfolioCard'

const API = window.__API_URL__ || import.meta.env.VITE_API_URL || ''

function Dashboard() {
  const { token, user, logout }         = useAuth()
  const navigate                        = useNavigate()
  const [portfolios, setPortfolios]     = useState([])
  const [newName, setNewName]           = useState('')
  const [creating, setCreating]         = useState(false)

  async function load() {
    try {
      const res = await fetch(`${API}/api/portfolios`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) setPortfolios(await res.json())
    } catch (e) {
      console.error('Failed to load portfolios:', e)
    }
  }

  useEffect(() => { load() }, [token])

  async function createPortfolio(e) {
    e.preventDefault()
    if (!newName.trim()) return
    setCreating(true)
    const res = await fetch(`${API}/api/portfolios`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName.trim(), life: 360 }),
    })
    if (res.ok) {
      setNewName('')
      load()
    }
    setCreating(false)
  }

  async function deletePortfolio(id) {
    await fetch(`${API}/api/portfolios/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    })
    setPortfolios(prev => prev.filter(p => p.id !== id))
  }

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Nav */}
      <header className="border-b border-gray-800 px-8 py-4 flex justify-between items-center">
        <h1 className="text-xl font-bold tracking-tight">rentSIM</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-400">{user?.email}</span>
          <button onClick={handleLogout} className="text-sm text-gray-400 hover:text-white transition-colors">
            Sign out
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-8 py-8 space-y-8">
        {/* Create portfolio */}
        <form onSubmit={createPortfolio} className="flex gap-3">
          <input
            type="text"
            placeholder="Portfolio name…"
            value={newName}
            onChange={e => setNewName(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-accent w-72"
          />
          <button
            type="submit" disabled={creating || !newName.trim()}
            className="bg-accent hover:bg-indigo-500 disabled:opacity-40 text-white font-semibold rounded-lg px-5 py-2 transition-all"
          >
            Create portfolio
          </button>
        </form>

        {portfolios.length === 0 && (
          <div className="text-center py-24 text-gray-500">
            <p className="text-lg">No portfolios yet.</p>
            <p className="text-sm mt-1">Create one above to start simulating.</p>
          </div>
        )}

        {portfolios.map(p => (
          <PortfolioCard key={p.id} portfolio={p} onDelete={() => deletePortfolio(p.id)} />
        ))}
      </main>
    </div>
  )
}

function RequireAuth({ children }) {
  const { user, ready } = useAuth()
  if (!ready) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="text-gray-500 text-sm animate-pulse">Loading…</div>
    </div>
  )
  return user ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login"    element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
    </Routes>
  )
}

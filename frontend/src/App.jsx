import { useEffect, useState } from 'react'
import { Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Login from './pages/Login'
import Register from './pages/Register'
import PortfolioCard from './components/PortfolioCard'

const API = window.__API_URL__ || import.meta.env.VITE_API_URL || ''

async function apiFetch(url, options = {}) {
  console.log(`[API] ${options.method || 'GET'} ${url}`)
  try {
    const res = await fetch(url, options)
    console.log(`[API] ${res.status} ${url}`)
    if (!res.ok) {
      const text = await res.text()
      console.error(`[API] Error body:`, text)
      throw new Error(`${res.status}: ${text}`)
    }
    return res
  } catch (e) {
    console.error(`[API] Failed: ${url}`, e)
    throw e
  }
}

function Dashboard() {
  const { token, user, logout }         = useAuth()
  const navigate                        = useNavigate()
  const [portfolios, setPortfolios]     = useState([])
  const [selectedId, setSelectedId]     = useState(null)
  const [loadError, setLoadError]       = useState('')
  const [newName, setNewName]           = useState('')
  const [creating, setCreating]         = useState(false)

  async function load() {
    if (!token) return
    setLoadError('')
    try {
      const res = await apiFetch(`${API}/api/portfolios`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json()
      setPortfolios(data)
      setSelectedId(prev => prev ?? (data[0]?.id ?? null))
    } catch (e) {
      setLoadError(e.message)
    }
  }

  useEffect(() => { load() }, [token])

  async function createPortfolio(e) {
    e.preventDefault()
    if (!newName.trim()) return
    setCreating(true)
    try {
      const res = await apiFetch(`${API}/api/portfolios`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName.trim(), life: 360 }),
      })
      const created = await res.json()
      setPortfolios(prev => [...prev, created])
      setSelectedId(created.id)
      setNewName('')
    } finally {
      setCreating(false)
    }
  }

  async function deletePortfolio(id) {
    await apiFetch(`${API}/api/portfolios/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    })
    setPortfolios(prev => {
      const next = prev.filter(p => p.id !== id)
      if (selectedId === id) setSelectedId(next[0]?.id ?? null)
      return next
    })
  }

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  const selected = portfolios.find(p => p.id === selectedId) ?? null

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

      <main className="max-w-7xl mx-auto px-8 py-8 space-y-6">
        {/* Portfolio tabs + create */}
        <div className="flex items-end gap-4 border-b border-gray-800 pb-0">
          <div className="flex gap-1 flex-1 overflow-x-auto">
            {portfolios.map(p => (
              <button
                key={p.id}
                onClick={() => setSelectedId(p.id)}
                className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 -mb-px transition-colors
                  ${selectedId === p.id
                    ? 'border-accent text-white'
                    : 'border-transparent text-gray-400 hover:text-gray-200'}`}
              >
                {p.name}
              </button>
            ))}
          </div>

          <form onSubmit={createPortfolio} className="flex gap-2 pb-2">
            <input
              type="text"
              placeholder="New portfolio…"
              value={newName}
              onChange={e => setNewName(e.target.value)}
              className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-accent w-48"
            />
            <button
              type="submit" disabled={creating || !newName.trim()}
              className="bg-accent hover:bg-indigo-500 disabled:opacity-40 text-white font-semibold rounded-lg px-4 py-1.5 text-sm transition-all"
            >
              + Create
            </button>
          </form>
        </div>

        {loadError && (
          <div className="bg-red-900/40 border border-red-700 rounded-lg px-4 py-3 text-red-300 text-sm">
            Failed to load portfolios: {loadError}
          </div>
        )}

        {portfolios.length === 0 && !loadError && (
          <div className="text-center py-24 text-gray-500">
            <p className="text-lg">No portfolios yet.</p>
            <p className="text-sm mt-1">Create one above to start simulating.</p>
          </div>
        )}

        {selected && (
          <PortfolioCard
            key={selected.id}
            portfolio={selected}
            onDelete={() => deletePortfolio(selected.id)}
          />
        )}
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

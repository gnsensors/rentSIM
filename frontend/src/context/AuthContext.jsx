import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'

const API = import.meta.env.VITE_API_URL || ''

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]   = useState(null)
  const [token, setToken] = useState(null)
  const [ready, setReady] = useState(false)
  const refreshTimer      = useRef(null)

  const scheduleRefresh = useCallback((delayMs) => {
    clearTimeout(refreshTimer.current)
    refreshTimer.current = setTimeout(doRefresh, delayMs)
  }, [])

  const doRefresh = useCallback(async () => {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 5000)
    try {
      const res = await fetch(`${API}/api/auth/refresh`, { method: 'POST', credentials: 'include', signal: controller.signal })
      if (!res.ok) { setUser(null); setToken(null); return }
      const data = await res.json()
      setToken(data.access_token)
      setUser(data.user)
      scheduleRefresh(13 * 60 * 1000)
    } catch {
      setUser(null)
      setToken(null)
    } finally {
      clearTimeout(timeout)
    }
  }, [scheduleRefresh])

  // Attempt silent refresh on mount
  useEffect(() => {
    doRefresh().finally(() => setReady(true))
    return () => clearTimeout(refreshTimer.current)
  }, [doRefresh])

  const login = useCallback(async (email, password) => {
    const res = await fetch(`${API}/api/auth/login`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) throw new Error((await res.json()).detail || 'Login failed')
    const data = await res.json()
    setToken(data.access_token)
    setUser(data.user)
    scheduleRefresh(13 * 60 * 1000)
    return data
  }, [scheduleRefresh])

  const register = useCallback(async (email, password) => {
    const res = await fetch(`${API}/api/auth/register`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) throw new Error((await res.json()).detail || 'Registration failed')
    const data = await res.json()
    setToken(data.access_token)
    setUser(data.user)
    scheduleRefresh(13 * 60 * 1000)
    return data
  }, [scheduleRefresh])

  const logout = useCallback(async () => {
    await fetch(`${API}/api/auth/logout`, { method: 'POST', credentials: 'include' })
    clearTimeout(refreshTimer.current)
    setUser(null)
    setToken(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, ready, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)

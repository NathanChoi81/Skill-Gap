import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../lib/api'
import { useAuth } from '../lib/auth'

interface MyRole {
  id: number
  name: string
  last_selected_at: string | null
}

export default function Roles() {
  const { user, refreshUser } = useAuth()
  const [q, setQ] = useState('')
  const [roles, setRoles] = useState<{ id: number; name: string }[]>([])
  const [myRoles, setMyRoles] = useState<MyRole[]>([])
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState<number | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get<MyRole[]>('/roles/my').then(setMyRoles).catch(() => setMyRoles([]))
  }, [user?.active_role_id])

  useEffect(() => {
    if (!q) {
      api.get<{ id: number; name: string }[]>('/roles/search?q=').then(setRoles).catch(() => setRoles([]))
      return
    }
    const t = setTimeout(() => {
      setLoading(true)
      api.get<{ id: number; name: string }[]>(`/roles/search?q=${encodeURIComponent(q)}`)
        .then(setRoles)
        .catch(() => setRoles([]))
        .finally(() => setLoading(false))
    }, 300)
    return () => clearTimeout(t)
  }, [q])

  const handleSelect = async (roleId: number) => {
    setError('')
    try {
      await api.post('/roles/select', { role_id: roleId })
      await refreshUser()
    } catch (e: unknown) {
      setError(getErrorMessage(e as { message?: string }))
    }
  }

  const handleAnalyze = async (roleId: number) => {
    setAnalyzing(roleId)
    setError('')
    try {
      await api.post(`/roles/${roleId}/analyze`)
    } catch (e: unknown) {
      setError(getErrorMessage(e as { message?: string }))
    } finally {
      setAnalyzing(null)
    }
  }

  const activeId = user?.active_role_id ?? null

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Roles</h1>
      {error && <div className="mb-4 text-sm text-red-600 bg-red-50 p-3 rounded">{error}</div>}
      <div className="mb-4">
        <input
          type="search"
          placeholder="Search roles"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-2 w-full max-w-md"
        />
      </div>
      {loading && <p className="text-gray-500">Searching…</p>}
      <ul className="space-y-2 mb-8">
        {roles.map((r) => (
          <li key={r.id} className="flex items-center gap-4 bg-white border rounded-lg p-4">
            <span className="font-medium">{r.name}</span>
            <button
              onClick={() => handleSelect(r.id)}
              className="text-sm bg-gray-200 hover:bg-gray-300 px-3 py-1 rounded"
            >
              {activeId === r.id ? 'Active' : 'Set active role'}
            </button>
            <button
              onClick={() => handleAnalyze(r.id)}
              disabled={analyzing === r.id}
              className="text-sm bg-blue-600 text-white hover:bg-blue-700 px-3 py-1 rounded disabled:opacity-50"
            >
              {analyzing === r.id ? 'Analyzing…' : 'Analyze Role'}
            </button>
          </li>
        ))}
      </ul>
      {myRoles.length > 0 && (
        <div>
          <h2 className="font-semibold text-gray-900 mb-2">Your role history</h2>
          <ul className="space-y-2">
            {myRoles.map((r) => (
              <li key={r.id} className="flex items-center gap-4 bg-gray-50 border rounded-lg p-3">
                <span className="font-medium">{r.name}</span>
                <button
                  onClick={() => handleSelect(r.id)}
                  className="text-sm bg-gray-200 hover:bg-gray-300 px-3 py-1 rounded"
                >
                  {activeId === r.id ? 'Active' : 'Set active role'}
                </button>
                <button
                  onClick={() => handleAnalyze(r.id)}
                  disabled={analyzing === r.id}
                  className="text-sm bg-blue-600 text-white hover:bg-blue-700 px-3 py-1 rounded disabled:opacity-50"
                >
                  {analyzing === r.id ? 'Analyzing…' : 'Analyze Role'}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

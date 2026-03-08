import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, getErrorMessage } from '../lib/api'
import { useAuth } from '../lib/auth'

interface Gap {
  skill_id: number
  name: string
  type: string
  frequency: number
}

export default function Skills() {
  const { user } = useAuth()
  const [gaps, setGaps] = useState<Gap[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [sort, setSort] = useState('frequency')
  const [typeFilter, setTypeFilter] = useState('')
  const [search, setSearch] = useState('')
  const roleId = user?.active_role_id

  const query = new URLSearchParams()
  query.set('sort', sort)
  if (typeFilter) query.set('type_filter', typeFilter)
  if (search) query.set('search', search)

  useEffect(() => {
    if (!roleId) {
      setGaps([])
      setLoading(false)
      return
    }
    setLoading(true)
    api.get<Gap[]>(`/roles/${roleId}/gaps?${query.toString()}`)
      .then(setGaps)
      .catch((e) => {
        setError(getErrorMessage(e as { message?: string }))
        setGaps([])
      })
      .finally(() => setLoading(false))
  }, [roleId, sort, typeFilter, search])

  const handleNotInterested = async (skillId: number, value: boolean) => {
    try {
      await api.post('/skills/not-interested', { skill_id: skillId, value })
      setNotInterested((prev) => {
        const next = new Set(prev)
        if (value) next.add(skillId)
        else next.delete(skillId)
        return next
      })
      if (roleId) {
        const list = await api.get<Gap[]>(`/roles/${roleId}/gaps`)
        setGaps(list)
      }
    } catch (e: unknown) {
      setError(getErrorMessage(e as { message?: string }))
    }
  }

  const addSkill = async (skillId: number) => {
    try {
      await api.post('/skills/add', { skill_id: skillId, source: 'manual' })
      if (roleId) {
        const list = await api.get<Gap[]>(`/roles/${roleId}/gaps`)
        setGaps(list)
      }
    } catch (e: unknown) {
      setError(getErrorMessage(e as { message?: string }))
    }
  }

  if (!roleId) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Skill Gaps</h1>
        <p className="text-gray-500">Select a role first.</p>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Skill Gap</h1>
      {error && <div className="mb-4 text-sm text-red-600 bg-red-50 p-3 rounded">{error}</div>}
      <div className="flex flex-wrap gap-4 mb-4">
        <label className="flex items-center gap-2">
          <span className="text-sm text-gray-700">Sort</span>
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            className="border border-gray-300 rounded-md px-2 py-1 text-sm"
          >
            <option value="frequency">Frequency</option>
            <option value="name">Alphabetical</option>
          </select>
        </label>
        <label className="flex items-center gap-2">
          <span className="text-sm text-gray-700">Type</span>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="border border-gray-300 rounded-md px-2 py-1 text-sm"
          >
            <option value="">All</option>
            <option value="required">Required</option>
            <option value="preferred">Preferred</option>
            <option value="description">Description</option>
          </select>
        </label>
        <label className="flex items-center gap-2">
          <span className="text-sm text-gray-700">Search</span>
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Skill name"
            className="border border-gray-300 rounded-md px-2 py-1 text-sm w-40"
          />
        </label>
      </div>
      {loading && <p className="text-gray-500">Loading…</p>}
      <div className="overflow-x-auto">
        <table className="min-w-full border border-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left">Skill</th>
              <th className="px-4 py-2 text-left">Type</th>
              <th className="px-4 py-2 text-left">Frequency</th>
              <th className="px-4 py-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {gaps.map((g) => (
              <tr key={g.skill_id} className="border-t">
                <td className="px-4 py-2">
                  <Link to={`/skills/${g.skill_id}`} className="text-blue-600 hover:underline">{g.name}</Link>
                </td>
                <td className="px-4 py-2">{g.type}</td>
                <td className="px-4 py-2">{g.frequency}</td>
                <td className="px-4 py-2 flex gap-2">
                  <button
                    onClick={() => addSkill(g.skill_id)}
                    className="text-sm bg-green-100 text-green-800 px-2 py-1 rounded hover:bg-green-200"
                  >
                    I have this skill
                  </button>
                  <button
                    onClick={() => handleNotInterested(g.skill_id, true)}
                    className="text-sm bg-gray-100 text-gray-700 px-2 py-1 rounded hover:bg-gray-200"
                    title="Not interested (global)"
                  >
                    Not interested
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../../lib/api'

interface UnmappedSkill {
  id: number
  name: string
}

export default function DevSkills() {
  const [skills, setSkills] = useState<UnmappedSkill[]>([])
  const [parentOptions, setParentOptions] = useState<{ id: number; name: string }[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [proposeResult, setProposeResult] = useState<{ applied: number } | null>(null)
  const [mappingChild, setMappingChild] = useState<number | null>(null)
  const [mappingParent, setMappingParent] = useState<number | null>(null)

  const loadUnmapped = () => {
    api.get<UnmappedSkill[]>('/dev/skills/unmapped')
      .then(setSkills)
      .catch((e) => {
        setError(getErrorMessage(e as { message?: string }))
        setSkills([])
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    setLoading(true)
    loadUnmapped()
    api.get<{ id: number; name: string }[]>('/skills/search?q=').then(setParentOptions).catch(() => setParentOptions([]))
  }, [])

  const handlePropose = async () => {
    setError('')
    try {
      const res = await api.post<{ applied: number }>('/dev/skills/propose-mappings')
      setProposeResult(res)
      loadUnmapped()
    } catch (e: unknown) {
      setError(getErrorMessage(e as { message?: string }))
    }
  }

  const handleSetParent = async () => {
    if (mappingChild == null || mappingParent == null) return
    setError('')
    try {
      await api.post('/dev/skills/map', { child_skill_id: mappingChild, parent_skill_id: mappingParent })
      setMappingChild(null)
      setMappingParent(null)
      loadUnmapped()
    } catch (e: unknown) {
      setError(getErrorMessage(e as { message?: string }))
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Dev: Skills</h1>
      {error && <div className="mb-4 text-sm text-red-600 bg-red-50 p-3 rounded">{error}</div>}
      {proposeResult && <p className="mb-4 text-green-600">Applied {proposeResult.applied} mapping(s).</p>}
      <button
        onClick={handlePropose}
        className="mb-4 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
      >
        Trigger AI mapping proposals
      </button>
      <h2 className="font-semibold text-gray-900 mb-2">Unmapped skills (set parent mappings)</h2>
      {loading && <p className="text-gray-500">Loading…</p>}
      <div className="space-y-4">
        <div className="flex flex-wrap gap-4 items-end">
          <label className="flex flex-col gap-1">
            <span className="text-sm text-gray-700">Child (unmapped)</span>
            <select
              value={mappingChild ?? ''}
              onChange={(e) => setMappingChild(e.target.value ? Number(e.target.value) : null)}
              className="border border-gray-300 rounded px-2 py-1 min-w-[180px]"
            >
              <option value="">Select skill</option>
              {skills.map((s) => (
                <option key={s.id} value={s.id}>{s.name} (id: {s.id})</option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-sm text-gray-700">Parent (canonical)</span>
            <select
              value={mappingParent ?? ''}
              onChange={(e) => setMappingParent(e.target.value ? Number(e.target.value) : null)}
              className="border border-gray-300 rounded px-2 py-1 min-w-[180px]"
            >
              <option value="">Select parent</option>
              {parentOptions.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </label>
          <button
            type="button"
            onClick={handleSetParent}
            disabled={mappingChild == null || mappingParent == null}
            className="bg-gray-700 text-white px-3 py-1 rounded text-sm disabled:opacity-50"
          >
            Set parent
          </button>
        </div>
        <ul className="space-y-1">
          {skills.map((s) => (
            <li key={s.id}>{s.name} (id: {s.id})</li>
          ))}
        </ul>
      </div>
    </div>
  )
}

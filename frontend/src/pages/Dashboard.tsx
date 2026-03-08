import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { api, getErrorMessage } from '../lib/api'

function ResumeUpload() {
  const [file, setFile] = useState<File | null>(null)
  const [useAi, setUseAi] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [msg, setMsg] = useState('')
  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return
    setUploading(true)
    setMsg('')
    const form = new FormData()
    form.append('file', file)
    form.append('use_ai', String(useAi))
    try {
      await fetch('/resumes/upload', { method: 'POST', credentials: 'include', body: form })
      setMsg('Resume uploaded.')
    } catch {
      setMsg('Upload failed.')
    } finally {
      setUploading(false)
    }
  }
  return (
    <div className="mb-6 p-4 bg-white border rounded-lg">
      <h2 className="font-semibold text-gray-900 mb-2">Upload resume (PDF)</h2>
      <form onSubmit={handleUpload} className="flex flex-wrap items-end gap-4">
        <input type="file" accept=".pdf" onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="text-sm" />
        <label className="flex items-center gap-1">
          <input type="checkbox" checked={useAi} onChange={(e) => setUseAi(e.target.checked)} />
          Use AI extraction
        </label>
        <button type="submit" disabled={!file || uploading} className="bg-blue-600 text-white px-3 py-1 rounded text-sm disabled:opacity-50">
          {uploading ? 'Uploading…' : 'Upload'}
        </button>
        {msg && <span className="text-sm text-gray-600">{msg}</span>}
      </form>
    </div>
  )
}

interface Summary {
  required_match: number
  preferred_match: number
  description_match: number
  internal_score: number
  label: string
  missing_count: number
  recommended_jobs: number
}

interface GapSkill {
  skill_id: number
  name: string
  type: string
  frequency: number
}

interface PlanCurrent {
  id: number
  deadline_date: string
  hours_per_week: number
  status?: string
  skills?: { skill_id: number; name: string }[]
}

export default function Dashboard() {
  const { user, refreshUser } = useAuth()
  const [summary, setSummary] = useState<Summary | null>(null)
  const [roles, setRoles] = useState<{ id: number; name: string }[]>([])
  const [selectedRoleId, setSelectedRoleId] = useState<number | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState('')
  const [mostNeededSkills, setMostNeededSkills] = useState<GapSkill[]>([])
  const [plan, setPlan] = useState<PlanCurrent | null>(null)

  useEffect(() => {
    api.get<{ id: number; name: string }[]>('/roles/search?q=').then(setRoles).catch(() => setRoles([]))
  }, [])

  const roleId = user?.active_role_id ?? selectedRoleId ?? roles[0]?.id

  useEffect(() => {
    if (!roleId) return
    setSelectedRoleId(roleId)
    api.get<Summary>(`/roles/${roleId}/summary`).then(setSummary).catch(() => setSummary(null))
    api.get<GapSkill[]>(`/roles/${roleId}/gaps?sort=frequency`).then((gaps) => setMostNeededSkills(gaps.slice(0, 5))).catch(() => setMostNeededSkills([]))
  }, [user?.active_role_id, roles, roleId])

  useEffect(() => {
    api.get<PlanCurrent>('/plan/current').then(setPlan).catch(() => setPlan(null))
  }, [])

  const handleSelectRole = async (roleId: number) => {
    setSelectedRoleId(roleId)
    try {
      await api.post('/roles/select', { role_id: roleId })
      await refreshUser()
      const s = await api.get<Summary>(`/roles/${roleId}/summary`)
      setSummary(s)
    } catch (e: unknown) {
      setError(getErrorMessage(e as { message?: string }))
    }
  }

  const handleAnalyze = async () => {
    if (!selectedRoleId) return
    setAnalyzing(true)
    setError('')
    try {
      await api.post(`/roles/${selectedRoleId}/analyze`)
      const s = await api.get<Summary>(`/roles/${selectedRoleId}/summary`)
      setSummary(s)
    } catch (e: unknown) {
      setError(getErrorMessage(e as { message?: string }))
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Dashboard</h1>
      <ResumeUpload />
      {error && <div className="mb-4 text-sm text-red-600 bg-red-50 p-3 rounded">{error}</div>}
      <div className="flex gap-4 items-center mb-6">
        <select
          value={selectedRoleId ?? ''}
          onChange={(e) => handleSelectRole(Number(e.target.value))}
          className="border border-gray-300 rounded-md px-3 py-2"
        >
          <option value="">Select role</option>
          {roles.map((r) => (
            <option key={r.id} value={r.id}>{r.name}</option>
          ))}
        </select>
        <button
          onClick={handleAnalyze}
          disabled={!selectedRoleId || analyzing}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {analyzing ? 'Analyzing…' : 'Analyze Role'}
        </button>
      </div>
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white border rounded-lg p-4">
            <p className="text-sm text-gray-500">Required match %</p>
            <p className="text-xl font-semibold">{summary.required_match}%</p>
          </div>
          <div className="bg-white border rounded-lg p-4">
            <p className="text-sm text-gray-500">Preferred match %</p>
            <p className="text-xl font-semibold">{summary.preferred_match}%</p>
          </div>
          <div className="bg-white border rounded-lg p-4">
            <p className="text-sm text-gray-500">Description match %</p>
            <p className="text-xl font-semibold">{summary.description_match}%</p>
          </div>
          <div className="bg-white border rounded-lg p-4">
            <p className="text-sm text-gray-500">Overall match label</p>
            <p className="text-xl font-semibold">{summary.label}</p>
          </div>
          <div className="bg-white border rounded-lg p-4">
            <p className="text-sm text-gray-500">Missing skills count</p>
            <p className="text-xl font-semibold">{summary.missing_count}</p>
          </div>
          <div className="bg-white border rounded-lg p-4">
            <p className="text-sm text-gray-500">Recommended jobs count</p>
            <p className="text-xl font-semibold">{summary.recommended_jobs}</p>
          </div>
        </div>
      )}
      {!summary && selectedRoleId && (
        <p className="text-gray-500 mb-6">Select a role and press Analyze Role to see metrics.</p>
      )}

      <div className="grid md:grid-cols-2 gap-6 mb-6">
        <div className="bg-white border rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-2">Most-needed skills (role)</h3>
          {mostNeededSkills.length ? (
            <ul className="list-disc list-inside text-sm text-gray-700">
              {mostNeededSkills.map((s) => (
                <li key={s.skill_id}>{s.name}</li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">Analyze a role to see top missing skills.</p>
          )}
        </div>
        <div className="bg-white border rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-2">Global popular skills</h3>
          <p className="text-sm text-gray-500">Based on job postings across roles. Coming soon.</p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-6">
        <div className="bg-white border rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-2">Deadline status</h3>
          {plan?.deadline_date ? (
            <p className="text-sm text-gray-700">Plan until {plan.deadline_date}</p>
          ) : (
            <p className="text-sm text-gray-500">No active plan. Set one in Plan.</p>
          )}
        </div>
        <div className="bg-white border rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-2">AI advisory summary</h3>
          {summary ? (
            <p className="text-sm text-gray-700">
              {summary.label === 'Ready'
                ? 'You are in a strong position for this role.'
                : summary.missing_count > 0
                  ? `Focus on the top ${Math.min(3, summary.missing_count)} missing skills to improve your match.`
                  : 'Analyze the role to get personalized advice.'}
            </p>
          ) : (
            <p className="text-sm text-gray-500">Select and analyze a role for advice.</p>
          )}
        </div>
      </div>

      <div className="flex gap-4 mt-6">
        <Link to="/resume-skills" className="text-blue-600 hover:underline">Resume & Skills</Link>
        <Link to="/jobs" className="text-blue-600 hover:underline">View Jobs</Link>
        <Link to="/skills" className="text-blue-600 hover:underline">View Skill Gaps</Link>
        <Link to="/plan" className="text-blue-600 hover:underline">Learning Plan</Link>
      </div>
    </div>
  )
}

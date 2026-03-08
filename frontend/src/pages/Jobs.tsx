import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, getErrorMessage } from '../lib/api'
import { useAuth } from '../lib/auth'

interface JobCard {
  id: number
  title_original: string
  label: string
  internal_score: number
  missing_skills: string[]
  missing_skill_ids: number[]
}

export default function Jobs() {
  const { user } = useAuth()
  const [jobs, setJobs] = useState<JobCard[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [sort, setSort] = useState('score')
  const [degree, setDegree] = useState('')
  const [experience, setExperience] = useState('')
  const [descMatch, setDescMatch] = useState('')
  const roleId = user?.active_role_id

  const query = new URLSearchParams()
  if (sort) query.set('sort', sort)
  if (degree) query.set('degree', degree)
  if (experience) query.set('experience', experience)
  if (descMatch) query.set('desc_match', descMatch)

  useEffect(() => {
    if (!roleId) {
      setJobs([])
      setLoading(false)
      return
    }
    setLoading(true)
    api.get<JobCard[]>(`/roles/${roleId}/jobs?${query.toString()}`)
      .then(setJobs)
      .catch((e) => {
        setError(getErrorMessage(e as { message?: string }))
        setJobs([])
      })
      .finally(() => setLoading(false))
  }, [roleId, sort, degree, experience, descMatch])

  const addSkill = async (skillId: number) => {
    try {
      await api.post('/skills/add', { skill_id: skillId, source: 'manual' })
      if (roleId) {
        const list = await api.get<JobCard[]>(`/roles/${roleId}/jobs`)
        setJobs(list)
      }
    } catch (e: unknown) {
      setError(getErrorMessage(e as { message?: string }))
    }
  }

  if (!roleId) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Jobs</h1>
        <p className="text-gray-500">Select a role on the Dashboard or Roles page first.</p>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Job Matches</h1>
      {error && <div className="mb-4 text-sm text-red-600 bg-red-50 p-3 rounded">{error}</div>}
      <div className="flex flex-wrap gap-4 mb-4">
        <label className="flex items-center gap-2">
          <span className="text-sm text-gray-700">Sort</span>
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            className="border border-gray-300 rounded-md px-2 py-1 text-sm"
          >
            <option value="score">By match score</option>
          </select>
        </label>
        <label className="flex items-center gap-2">
          <span className="text-sm text-gray-700">Degree</span>
          <input
            type="text"
            value={degree}
            onChange={(e) => setDegree(e.target.value)}
            placeholder="Filter"
            className="border border-gray-300 rounded-md px-2 py-1 text-sm w-28"
          />
        </label>
        <label className="flex items-center gap-2">
          <span className="text-sm text-gray-700">Experience</span>
          <input
            type="text"
            value={experience}
            onChange={(e) => setExperience(e.target.value)}
            placeholder="Filter"
            className="border border-gray-300 rounded-md px-2 py-1 text-sm w-28"
          />
        </label>
        <label className="flex items-center gap-2">
          <span className="text-sm text-gray-700">Desc match %</span>
          <input
            type="text"
            value={descMatch}
            onChange={(e) => setDescMatch(e.target.value)}
            placeholder="Min %"
            className="border border-gray-300 rounded-md px-2 py-1 text-sm w-20"
          />
        </label>
      </div>
      {loading && <p className="text-gray-500">Loading jobs…</p>}
      <div className="space-y-4">
        {jobs.map((job) => (
          <div key={job.id} className="bg-white border rounded-lg p-4">
            <div className="flex justify-between items-start">
              <div>
                <span className="font-medium text-gray-900">{job.title_original}</span>
                <span className="ml-2 text-sm text-gray-500">Match: {job.label}</span>
              </div>
              <Link to={`/jobs/${job.id}`} className="text-sm text-blue-600 hover:underline">View details</Link>
            </div>
            <p className="text-xs text-gray-500 mt-1">Missing skills preview: {job.missing_skills.slice(0, 3).join(', ')}{job.missing_skills.length > 3 ? '…' : ''}</p>
            <details className="mt-2">
              <summary className="text-sm text-gray-600 cursor-pointer hover:text-gray-900">Full missing skills list ({job.missing_skills.length})</summary>
              <ul className="mt-2 pl-4 space-y-1">
                {job.missing_skills.map((name, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm">
                    <span>{name}</span>
                    <button
                      onClick={() => job.missing_skill_ids[i] != null && addSkill(job.missing_skill_ids[i])}
                      className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded hover:bg-green-200"
                    >
                      I have this skill
                    </button>
                  </li>
                ))}
              </ul>
            </details>
          </div>
        ))}
      </div>
    </div>
  )
}

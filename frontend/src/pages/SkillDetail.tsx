import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, getErrorMessage } from '../lib/api'
import { useAuth } from '../lib/auth'

interface CourseItem {
  id: number
  title: string
  difficulty: number
  duration_hours: number
  format: string
  popularity_score: number
  url: string | null
  status: string | null
}

interface GapSkill {
  skill_id: number
  name: string
  type: string
  frequency: number
}

export default function SkillDetail() {
  const { skillId } = useParams<{ skillId: string }>()
  const { user } = useAuth()
  const [skillName, setSkillName] = useState('')
  const [importance, setImportance] = useState<number | null>(null)
  const [contextType, setContextType] = useState('')
  const [courses, setCourses] = useState<CourseItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const roleId = user?.active_role_id
  const id = skillId ? parseInt(skillId, 10) : null

  useEffect(() => {
    if (!id) return
    setLoading(true)
    setError('')
    Promise.all([
      api.get<{ id: number; name: string }>(`/skills/${id}`).then((s) => setSkillName(s.name)).catch(() => setSkillName('')),
      roleId
        ? api.get<GapSkill[]>(`/roles/${roleId}/gaps`).then((gaps) => {
            const g = gaps.find((x) => x.skill_id === id)
            if (g) {
              setImportance(g.frequency)
              setContextType(g.type)
            }
          }).catch(() => {})
        : Promise.resolve(),
      api.get<CourseItem[]>(`/skills/${id}/courses`).then(setCourses).catch((e) => {
        setError(getErrorMessage(e as { message?: string }))
        setCourses([])
      }),
    ]).finally(() => setLoading(false))
  }, [id, roleId])

  const setStatus = async (courseId: number, status: 'in_progress' | 'complete') => {
    try {
      await api.post(`/courses/${courseId}/status`, { status })
      if (skillId) {
        const list = await api.get<CourseItem[]>(`/skills/${skillId}/courses`)
        setCourses(list)
      }
    } catch (e: unknown) {
      setError(getErrorMessage(e as { message?: string }))
    }
  }

  return (
    <div>
      <p className="text-sm text-gray-500 mb-1"><Link to="/skills" className="text-blue-600 hover:underline">Skill Gap</Link></p>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">{skillName || 'Skill'}</h1>
      {importance != null && <p className="text-sm text-gray-600 mb-1">Importance (frequency in role): {importance}</p>}
      {contextType && <p className="text-sm text-gray-600 mb-4">Context: {contextType} (required/preferred/description)</p>}
      {error && <div className="mb-4 text-sm text-red-600 bg-red-50 p-3 rounded">{error}</div>}
      {loading && <p className="text-gray-500">Loading…</p>}
      <h2 className="font-semibold text-gray-900 mt-4 mb-2">Learning resources</h2>
      <div className="grid gap-4 md:grid-cols-2">
        {courses.map((c) => (
          <div key={c.id} className="bg-white border rounded-lg p-4">
            <h3 className="font-medium">{c.title}</h3>
            <p className="text-sm text-gray-500">
              Difficulty {c.difficulty} (adjusted) · {c.duration_hours}h · {c.format} · Popularity {c.popularity_score}
            </p>
            {c.url && (
              <a href={c.url} target="_blank" rel="noreferrer" className="text-sm text-blue-600 hover:underline">
                Link
              </a>
            )}
            <div className="mt-2 flex gap-2 items-center">
              <button
                onClick={() => setStatus(c.id, 'in_progress')}
                className="text-sm bg-yellow-100 px-2 py-1 rounded hover:bg-yellow-200"
              >
                Mark in progress
              </button>
              <button
                onClick={() => setStatus(c.id, 'complete')}
                className="text-sm bg-green-100 px-2 py-1 rounded hover:bg-green-200"
              >
                Mark complete
              </button>
              {c.status && <span className="text-sm text-gray-500">({c.status})</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

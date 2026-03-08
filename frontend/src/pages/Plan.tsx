import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../lib/api'
import { useAuth } from '../lib/auth'

interface ProposedSkill {
  skill_id: number
  name: string
  estimated_hours: number
  priority: number
}

interface PlanProposal {
  skills: ProposedSkill[]
  total_hours: number
  budget_hours: number
  warning: string
}

interface CurrentPlan {
  id: number
  deadline_date: string
  hours_per_week: number
  status: string
  skills: { skill_id: number; name: string }[]
}

function reorderArray<T>(arr: T[], fromIndex: number, toIndex: number): T[] {
  const out = [...arr]
  const [item] = out.splice(fromIndex, 1)
  out.splice(toIndex, 0, item)
  return out
}

export default function Plan() {
  const { user } = useAuth()
  const [current, setCurrent] = useState<CurrentPlan | null>(null)
  const [deadlineMode, setDeadlineMode] = useState<'weeks' | 'months' | 'date'>('weeks')
  const [weeks, setWeeks] = useState(12)
  const [months, setMonths] = useState(3)
  const [date, setDate] = useState('')
  const [hoursPerWeek, setHoursPerWeek] = useState(5)
  const [proposal, setProposal] = useState<PlanProposal | null>(null)
  const [ordering, setOrdering] = useState<number[]>([])
  const [step, setStep] = useState<'input' | 'review' | null>(null)
  const [error, setError] = useState('')
  const roleId = user?.active_role_id

  useEffect(() => {
    api.get<CurrentPlan | null>('/plan/current').then(setCurrent).catch(() => setCurrent(null))
  }, [])

  const getDeadlineDate = (): string => {
    const today = new Date()
    if (deadlineMode === 'weeks') {
      const d = new Date(today)
      d.setDate(d.getDate() + weeks * 7)
      return d.toISOString().slice(0, 10)
    }
    if (deadlineMode === 'months') {
      const d = new Date(today)
      d.setMonth(d.getMonth() + months)
      return d.toISOString().slice(0, 10)
    }
    return date || new Date(today.getTime() + 90 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
  }

  const handlePropose = async () => {
    if (!roleId) {
      setError('Select a role first.')
      return
    }
    setError('')
    const deadline = getDeadlineDate()
    try {
      const res = await api.post<PlanProposal>('/plan/propose', { deadline, hours_per_week: hoursPerWeek })
      setProposal(res)
      setOrdering(res.skills.map((s) => s.skill_id))
      setStep('review')
    } catch (e: unknown) {
      setError(getErrorMessage(e as { message?: string }))
    }
  }

  const removeFromProposal = (skillId: number) => {
    setOrdering((prev) => prev.filter((id) => id !== skillId))
  }

  const moveInProposal = (index: number, direction: 'up' | 'down') => {
    setOrdering((prev) => {
      const next = direction === 'up' ? index - 1 : index + 1
      if (next < 0 || next >= prev.length) return prev
      return reorderArray(prev, index, next)
    })
  }

  const handleConfirm = async () => {
    if (!proposal) return
    setError('')
    const skillsToConfirm = ordering.filter((id) => proposal.skills.some((s) => s.skill_id === id))
    if (skillsToConfirm.length === 0) {
      setError('Keep at least one skill.')
      return
    }
    try {
      await api.post('/plan/confirm', {
        skills: skillsToConfirm,
        ordering: skillsToConfirm,
        deadline: getDeadlineDate(),
        hours_per_week: hoursPerWeek,
      })
      const plan = await api.get<CurrentPlan>('/plan/current')
      setCurrent(plan)
      setProposal(null)
      setStep(null)
    } catch (e: unknown) {
      setError(getErrorMessage(e as { message?: string }))
    }
  }

  const setPlanStatus = async (status: 'active' | 'paused') => {
    try {
      await api.patch('/plan/current', { status })
      const plan = await api.get<CurrentPlan>('/plan/current')
      setCurrent(plan)
    } catch (e: unknown) {
      setError(getErrorMessage(e as { message?: string }))
    }
  }

  if (current && !step) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Learning Plan — Roadmap</h1>
        <p className="text-gray-600">
          Deadline: {current.deadline_date} · {current.hours_per_week} hrs/week · Status: {current.status}
        </p>
        <div className="mt-4 flex gap-2">
          {current.status === 'active' && (
            <button
              onClick={() => setPlanStatus('paused')}
              className="bg-amber-100 text-amber-800 px-3 py-1 rounded text-sm hover:bg-amber-200"
            >
              Pause plan
            </button>
          )}
          {current.status === 'paused' && (
            <button
              onClick={() => setPlanStatus('active')}
              className="bg-green-100 text-green-800 px-3 py-1 rounded text-sm hover:bg-green-200"
            >
              Resume plan
            </button>
          )}
        </div>
        <h2 className="font-semibold text-gray-900 mt-4 mb-2">Ordered skill sequence</h2>
        <ol className="list-decimal list-inside space-y-1">
          {current.skills.map((s) => (
            <li key={s.skill_id}>{s.name}</li>
          ))}
        </ol>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Learning Plan</h1>
      {error && <div className="mb-4 text-sm text-red-600 bg-red-50 p-3 rounded">{error}</div>}
      {!roleId && <p className="text-gray-500">Select a role first.</p>}
      {step === 'input' && roleId && (
        <div className="space-y-4 max-w-md">
          <div>
            <label className="block text-sm font-medium text-gray-700">Deadline</label>
            <select
              value={deadlineMode}
              onChange={(e) => setDeadlineMode(e.target.value as 'weeks' | 'months' | 'date')}
              className="mt-1 border border-gray-300 rounded-md px-3 py-2 w-full"
            >
              <option value="weeks">In weeks</option>
              <option value="months">In months</option>
              <option value="date">By date</option>
            </select>
            {deadlineMode === 'weeks' && (
              <input
                type="number"
                min={1}
                value={weeks}
                onChange={(e) => setWeeks(Number(e.target.value))}
                className="mt-2 border border-gray-300 rounded-md px-3 py-2 w-full"
              />
            )}
            {deadlineMode === 'months' && (
              <input
                type="number"
                min={1}
                value={months}
                onChange={(e) => setMonths(Number(e.target.value))}
                className="mt-2 border border-gray-300 rounded-md px-3 py-2 w-full"
              />
            )}
            {deadlineMode === 'date' && (
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="mt-2 border border-gray-300 rounded-md px-3 py-2 w-full"
              />
            )}
            <p className="mt-1 text-xs text-gray-500">Target date: {getDeadlineDate()}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Hours per week</label>
            <input
              type="number"
              min={1}
              max={40}
              value={hoursPerWeek}
              onChange={(e) => setHoursPerWeek(Number(e.target.value))}
              className="mt-1 border border-gray-300 rounded-md px-3 py-2 w-full"
            />
          </div>
          <button
            onClick={handlePropose}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            Propose plan
          </button>
        </div>
      )}
      {step === 'review' && proposal && (
        <div className="space-y-4">
          {proposal.warning && <p className="text-amber-600">{proposal.warning}</p>}
          <p>Total: {proposal.total_hours}h · Budget: {proposal.budget_hours}h</p>
          <p className="text-sm text-gray-600">Remove or reorder skills, then confirm.</p>
          <ul className="space-y-2">
            {ordering
              .map((skillId) => proposal.skills.find((s) => s.skill_id === skillId))
              .filter(Boolean)
              .map((s, index) => (
                <li key={s!.skill_id} className="flex items-center gap-2 bg-gray-50 rounded px-3 py-2">
                  <span className="flex-1">{s!.name} — {s!.estimated_hours}h</span>
                  <button
                    type="button"
                    onClick={() => moveInProposal(index, 'up')}
                    disabled={index === 0}
                    className="text-sm text-gray-600 hover:text-gray-900 disabled:opacity-50"
                  >
                    ↑
                  </button>
                  <button
                    type="button"
                    onClick={() => moveInProposal(index, 'down')}
                    disabled={index === ordering.length - 1}
                    className="text-sm text-gray-600 hover:text-gray-900 disabled:opacity-50"
                  >
                    ↓
                  </button>
                  <button
                    type="button"
                    onClick={() => removeFromProposal(s!.skill_id)}
                    className="text-sm text-red-600 hover:underline"
                  >
                    Remove
                  </button>
                </li>
              ))}
          </ul>
          <button
            onClick={handleConfirm}
            className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
          >
            Confirm plan
          </button>
          <button
            onClick={() => { setStep('input'); setProposal(null); }}
            className="ml-2 bg-gray-200 text-gray-800 px-4 py-2 rounded-md hover:bg-gray-300"
          >
            Back
          </button>
        </div>
      )}
      {!step && !current && roleId && (
        <div>
          <p className="text-gray-600 mb-4">Create a deadline-driven learning plan.</p>
          <button
            onClick={() => setStep('input')}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            Create plan
          </button>
        </div>
      )}
    </div>
  )
}

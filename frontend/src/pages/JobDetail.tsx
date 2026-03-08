import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api, getErrorMessage } from '../lib/api'

interface JobDetailData {
  id: number
  title_original: string
  what_you_will_do_excerpt: string
  label: string
  required: string[]
  preferred: string[]
  description: string[]
  missing_skills: string[]
}

export default function JobDetail() {
  const { jobId } = useParams<{ jobId: string }>()
  const [job, setJob] = useState<JobDetailData | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!jobId) return
    api.get<JobDetailData>(`/jobs/${jobId}`)
      .then(setJob)
      .catch((e) => {
        setError(getErrorMessage(e as { message?: string }))
        setJob(null)
      })
  }, [jobId])

  if (error) return <div className="p-4 text-red-600">{error}</div>
  if (!job) return <div className="p-4">Loading…</div>

  return (
    <div>
      <Link to="/jobs" className="text-blue-600 hover:underline mb-4 inline-block">← Back to Jobs</Link>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">{job.title_original}</h1>
      <p className="text-sm text-gray-500 mb-4">Match: {job.label}</p>
      {job.what_you_will_do_excerpt && (
        <div className="mb-4">
          <h2 className="font-semibold text-gray-900 mb-1">What you will do</h2>
          <p className="text-gray-700 whitespace-pre-wrap">{job.what_you_will_do_excerpt}</p>
        </div>
      )}
      <div className="grid gap-4 md:grid-cols-3">
        <div>
          <h3 className="font-medium text-gray-900 mb-1">Required</h3>
          <ul className="list-disc pl-4">{job.required.map((s, i) => <li key={i}>{s}</li>)}</ul>
        </div>
        <div>
          <h3 className="font-medium text-gray-900 mb-1">Preferred</h3>
          <ul className="list-disc pl-4">{job.preferred.map((s, i) => <li key={i}>{s}</li>)}</ul>
        </div>
        <div>
          <h3 className="font-medium text-gray-900 mb-1">Description</h3>
          <ul className="list-disc pl-4">{job.description.map((s, i) => <li key={i}>{s}</li>)}</ul>
        </div>
      </div>
      {job.missing_skills.length > 0 && (
        <div className="mt-4">
          <h3 className="font-medium text-gray-900 mb-1">Missing skills for you</h3>
          <ul className="list-disc pl-4">{job.missing_skills.map((s, i) => <li key={i}>{s}</li>)}</ul>
        </div>
      )}
    </div>
  )
}

import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../../lib/api'

interface DevJob {
  id: number
  title_original: string
  role_id: number | null
  role_name: string | null
  degree_required: string | null
  experience_required: string | null
}

export default function DevJobs() {
  const [files, setFiles] = useState<FileList | null>(null)
  const [result, setResult] = useState<{ uploaded: number; jobs: { id: number; title_original: string }[] } | null>(null)
  const [jobs, setJobs] = useState<DevJob[]>([])
  const [roles, setRoles] = useState<{ id: number; name: string }[]>([])
  const [error, setError] = useState('')

  const loadJobs = () => {
    api.get<DevJob[]>('/dev/jobs').then(setJobs).catch(() => setJobs([]))
  }

  useEffect(() => {
    loadJobs()
    api.get<{ id: number; name: string }[]>('/roles/search?q=').then(setRoles).catch(() => setRoles([]))
  }, [])

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!files?.length) return
    setError('')
    const form = new FormData()
    for (let i = 0; i < files.length; i++) {
      form.append('files', files[i])
    }
    try {
      const res = await fetch('/dev/jobs/upload', {
        method: 'POST',
        credentials: 'include',
        body: form,
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data?.message || 'Upload failed')
      setResult(data)
      loadJobs()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    }
  }

  const handleOverrideRole = async (jobId: number, roleId: number) => {
    try {
      await api.patch(`/dev/jobs/${jobId}`, { role_id: roleId })
      loadJobs()
    } catch (e: unknown) {
      setError(getErrorMessage(e as { message?: string }))
    }
  }

  const handleDelete = async (jobId: number) => {
    try {
      await api.delete(`/dev/jobs/${jobId}`)
      loadJobs()
    } catch (e: unknown) {
      setError(getErrorMessage(e as { message?: string }))
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Dev: Jobs</h1>
      {error && <div className="mb-4 text-sm text-red-600 bg-red-50 p-3 rounded">{error}</div>}
      <form onSubmit={handleUpload} className="mb-8 p-4 bg-gray-50 rounded-lg">
        <h2 className="font-semibold text-gray-900 mb-2">Upload synthetic job PDFs</h2>
        <input
          type="file"
          accept=".pdf"
          multiple
          onChange={(e) => setFiles(e.target.files || null)}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-blue-50 file:text-blue-700"
        />
        <button type="submit" className="mt-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
          Upload
        </button>
      </form>
      {result && <p className="mb-4 text-green-600">Uploaded {result.uploaded} job(s).</p>}
      <h2 className="font-semibold text-gray-900 mb-2">Parsed job data</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full border border-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left">ID</th>
              <th className="px-4 py-2 text-left">Title</th>
              <th className="px-4 py-2 text-left">Role</th>
              <th className="px-4 py-2 text-left">Degree</th>
              <th className="px-4 py-2 text-left">Experience</th>
              <th className="px-4 py-2 text-left">Override role</th>
              <th className="px-4 py-2 text-left">Delete</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((j) => (
              <tr key={j.id} className="border-t">
                <td className="px-4 py-2">{j.id}</td>
                <td className="px-4 py-2">{j.title_original}</td>
                <td className="px-4 py-2">{j.role_name ?? '—'}</td>
                <td className="px-4 py-2 text-sm">{j.degree_required ?? '—'}</td>
                <td className="px-4 py-2 text-sm">{j.experience_required ?? '—'}</td>
                <td className="px-4 py-2">
                  <select
                    value={j.role_id ?? ''}
                    onChange={(e) => handleOverrideRole(j.id, Number(e.target.value))}
                    className="border border-gray-300 rounded px-2 py-1 text-sm"
                  >
                    <option value="">—</option>
                    {roles.map((r) => (
                      <option key={r.id} value={r.id}>{r.name}</option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-2">
                  <button
                    type="button"
                    onClick={() => handleDelete(j.id)}
                    className="text-sm text-red-600 hover:underline"
                  >
                    Delete
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

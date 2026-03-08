import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../lib/api'

interface MySkill {
  id: number
  name: string
  source: string
}

const SOURCES = ['all', 'resume', 'manual', 'course'] as const

export default function ResumeSkills() {
  const [file, setFile] = useState<File | null>(null)
  const [useAi, setUseAi] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState('')
  const [mySkills, setMySkills] = useState<MySkill[]>([])
  const [sourceFilter, setSourceFilter] = useState<string>('all')
  const [addQuery, setAddQuery] = useState('')
  const [searchResults, setSearchResults] = useState<{ id: number; name: string }[]>([])
  const [error, setError] = useState('')

  const loadMySkills = () => {
    api.get<MySkill[]>('/skills/my').then(setMySkills).catch(() => setMySkills([]))
  }

  useEffect(() => {
    loadMySkills()
  }, [])

  useEffect(() => {
    if (!addQuery.trim()) {
      setSearchResults([])
      return
    }
    const t = setTimeout(() => {
      api.get<{ id: number; name: string }[]>(`/skills/search?q=${encodeURIComponent(addQuery)}&limit=15`)
        .then(setSearchResults)
        .catch(() => setSearchResults([]))
    }, 200)
    return () => clearTimeout(t)
  }, [addQuery])

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return
    setUploading(true)
    setUploadMsg('')
    setError('')
    const form = new FormData()
    form.append('file', file)
    form.append('use_ai', String(useAi))
    try {
      await fetch('/resumes/upload', { method: 'POST', credentials: 'include', body: form })
      setUploadMsg('Resume uploaded. Skills updated.')
      loadMySkills()
    } catch {
      setUploadMsg('')
      setError('Upload failed.')
    } finally {
      setUploading(false)
    }
  }

  const handleRemove = async (skillId: number) => {
    try {
      await api.post('/skills/remove', { skill_id: skillId })
      loadMySkills()
    } catch (e: unknown) {
      setError(getErrorMessage(e as { message?: string }))
    }
  }

  const handleAddSkill = async (skillId: number) => {
    try {
      await api.post('/skills/add', { skill_id: skillId, source: 'manual' })
      loadMySkills()
      setAddQuery('')
      setSearchResults([])
    } catch (e: unknown) {
      setError(getErrorMessage(e as { message?: string }))
    }
  }

  const filtered = sourceFilter === 'all'
    ? mySkills
    : mySkills.filter((s) => s.source === sourceFilter)

  const bySource = filtered.reduce<Record<string, MySkill[]>>((acc, s) => {
    (acc[s.source] ??= []).push(s)
    return acc
  }, {})

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Resume & Skills</h1>
      {error && <div className="mb-4 text-sm text-red-600 bg-red-50 p-3 rounded">{error}</div>}

      {/* Resume PDF upload + AI toggle */}
      <div className="mb-6 p-4 bg-white border rounded-lg">
        <h2 className="font-semibold text-gray-900 mb-2">Resume PDF upload</h2>
        <form onSubmit={handleUpload} className="flex flex-wrap items-end gap-4">
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="text-sm"
          />
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={useAi} onChange={(e) => setUseAi(e.target.checked)} />
            AI mode (extract skills with AI)
          </label>
          <button
            type="submit"
            disabled={!file || uploading}
            className="bg-blue-600 text-white px-3 py-2 rounded text-sm disabled:opacity-50"
          >
            {uploading ? 'Uploading…' : 'Upload'}
          </button>
          {uploadMsg && <span className="text-sm text-green-600">{uploadMsg}</span>}
        </form>
        <p className="text-xs text-gray-500 mt-2">
          Uploading replaces your previous resume and removes only resume-sourced skills.
        </p>
      </div>

      {/* Manual skill add */}
      <div className="mb-6 p-4 bg-white border rounded-lg">
        <h2 className="font-semibold text-gray-900 mb-2">Add skill manually</h2>
        <input
          type="text"
          value={addQuery}
          onChange={(e) => setAddQuery(e.target.value)}
          placeholder="Search skills…"
          className="w-full max-w-xs border border-gray-300 rounded-md px-3 py-2 text-sm"
        />
        {searchResults.length > 0 && (
          <ul className="mt-2 border border-gray-200 rounded-md divide-y max-h-48 overflow-auto">
            {searchResults.map((s) => (
              <li key={s.id} className="flex items-center justify-between px-3 py-2 text-sm">
                <span>{s.name}</span>
                <button
                  type="button"
                  onClick={() => handleAddSkill(s.id)}
                  className="text-blue-600 hover:underline"
                >
                  Add
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Source filter */}
      <div className="mb-2 flex items-center gap-2">
        <span className="text-sm font-medium text-gray-700">Source filter:</span>
        <select
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value)}
          className="border border-gray-300 rounded-md px-2 py-1 text-sm"
        >
          {SOURCES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {/* Extracted / mapped skills list with source and remove */}
      <div className="bg-white border rounded-lg p-4">
        <h2 className="font-semibold text-gray-900 mb-2">Your skills (with source)</h2>
        {filtered.length === 0 ? (
          <p className="text-sm text-gray-500">No skills yet. Upload a resume or add skills manually.</p>
        ) : (
          <div className="space-y-4">
            {Object.entries(bySource).map(([source, skills]) => (
              <div key={source}>
                <h3 className="text-sm font-medium text-gray-600 capitalize">{source}</h3>
                <ul className="mt-1 flex flex-wrap gap-2">
                  {skills.map((s) => (
                    <li
                      key={s.id}
                      className="inline-flex items-center gap-1 bg-gray-100 rounded px-2 py-1 text-sm"
                    >
                      <span>{s.name}</span>
                      <button
                        type="button"
                        onClick={() => handleRemove(s.id)}
                        className="text-red-600 hover:underline text-xs"
                        aria-label={`Remove ${s.name}`}
                      >
                        Remove
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

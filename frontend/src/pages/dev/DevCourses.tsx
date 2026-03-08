import { useState } from 'react'

export default function DevCourses() {
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<{ uploaded: number } | null>(null)
  const [error, setError] = useState('')

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return
    setError('')
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch('/dev/courses/upload', {
        method: 'POST',
        credentials: 'include',
        body: form,
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data?.message || 'Upload failed')
      setResult(data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Dev: Upload courses.json</h1>
      {error && <div className="mb-4 text-sm text-red-600 bg-red-50 p-3 rounded">{error}</div>}
      <form onSubmit={handleUpload} className="space-y-4">
        <input
          type="file"
          accept=".json"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-blue-50 file:text-blue-700"
        />
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
          Upload
        </button>
      </form>
      {result && <p className="mt-4 text-green-600">Uploaded {result.uploaded} course(s).</p>}
    </div>
  )
}

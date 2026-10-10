import { useState, type FormEvent } from 'react'
import { uploadFile } from '../api'
import type { UploadResult } from '../types'

interface Props {
  onUploaded: (result: UploadResult, fileName: string) => void
}

export default function UploadForm({ onUploaded }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!file) return
    setBusy(true)
    setError(null)
    try {
      const result = await uploadFile(file)
      onUploaded(result, file.name)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <label className="file-picker">
        <span>Orders file (.csv, .xlsx or .xls, up to 10 MB)</span>
        <input
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
      </label>
      <button type="submit" disabled={!file || busy}>
        {busy ? 'Processing…' : 'Run automation'}
      </button>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
    </form>
  )
}

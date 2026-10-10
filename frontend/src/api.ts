import type { ReportKind, RunDetail, RunListItem, UploadResult } from './types'

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message)
    this.name = 'ApiError'
  }
}

async function readError(response: Response): Promise<ApiError> {
  let message = `Request failed (HTTP ${response.status})`
  try {
    const body = await response.json()
    if (typeof body?.detail === 'string') message = body.detail
  } catch {
    // Non-JSON error body: keep the generic message.
  }
  return new ApiError(message, response.status)
}

export async function uploadFile(file: File): Promise<UploadResult> {
  const form = new FormData()
  form.append('file', file)
  const response = await fetch('/api/runs', { method: 'POST', body: form })
  if (!response.ok) throw await readError(response)
  return response.json()
}

export async function listRuns(): Promise<RunListItem[]> {
  const response = await fetch('/api/runs')
  if (!response.ok) throw await readError(response)
  return response.json()
}

export async function getRun(runId: string): Promise<RunDetail> {
  const response = await fetch(`/api/runs/${encodeURIComponent(runId)}`)
  if (!response.ok) throw await readError(response)
  return response.json()
}

export function reportUrl(runId: string, kind: ReportKind): string {
  return `/api/runs/${encodeURIComponent(runId)}/files/${kind}`
}

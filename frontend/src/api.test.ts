import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, getRun, listRuns, reportUrl, uploadFile } from './api'

const fetchMock = vi.fn()

beforeEach(() => {
  fetchMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('uploadFile', () => {
  it('posts the file as multipart form data and returns the parsed result', async () => {
    const payload = { run_id: 'r1', summary: { total_records: 1, valid_records: 1, rejected_records: 0, duplicates_detected: 0 } }
    fetchMock.mockResolvedValue(jsonResponse(payload, 201))

    const file = new File(['a'], 'orders.csv', { type: 'text/csv' })
    const result = await uploadFile(file)

    expect(result).toEqual(payload)
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/runs')
    expect(init.method).toBe('POST')
    expect((init.body as FormData).get('file')).toBeInstanceOf(File)
  })

  it('surfaces the server detail message as an ApiError', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'Missing required columns: amount.' }, 400))

    await expect(uploadFile(new File(['x'], 'bad.csv'))).rejects.toThrow('Missing required columns: amount.')
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'nope' }, 400))
    await expect(uploadFile(new File(['x'], 'bad.csv'))).rejects.toBeInstanceOf(ApiError)
  })

  it('falls back to a generic message when the error body is not JSON', async () => {
    fetchMock.mockResolvedValue(new Response('<html>oops</html>', { status: 500 }))
    await expect(uploadFile(new File(['x'], 'a.csv'))).rejects.toThrow('Request failed (HTTP 500)')
  })
})

describe('listRuns and getRun', () => {
  it('lists runs', async () => {
    fetchMock.mockResolvedValue(jsonResponse([{ run_id: 'a' }]))
    expect(await listRuns()).toEqual([{ run_id: 'a' }])
    expect(fetchMock.mock.calls[0][0]).toBe('/api/runs')
  })

  it('encodes the run id in the URL', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ run_id: 'a b' }))
    await getRun('a b')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/runs/a%20b')
  })
})

describe('reportUrl', () => {
  it('builds download URLs for each report kind', () => {
    expect(reportUrl('run_1', 'cleaned')).toBe('/api/runs/run_1/files/cleaned')
    expect(reportUrl('run_1', 'input')).toBe('/api/runs/run_1/files/input')
  })
})

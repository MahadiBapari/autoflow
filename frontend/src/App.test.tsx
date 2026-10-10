import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import * as api from './api'
import type { RunDetail } from './types'

vi.mock('./api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./api')>()
  return { ...actual, listRuns: vi.fn(), getRun: vi.fn(), uploadFile: vi.fn() }
})

const detail: RunDetail = {
  run_id: 'orders_sample_1',
  summary: {
    total_records: 2,
    valid_records: 1,
    rejected_records: 1,
    duplicates_detected: 0,
    input_file: 'orders_sample.csv',
  },
  cleaned: [{ order_id: 'ORD-1001', customer_name: 'John Smith' }],
  rejected: [{ order_id: 'ORD-1002', rejection_reason: 'invalid amount' }],
}

beforeEach(() => {
  vi.mocked(api.listRuns).mockResolvedValue([])
  vi.mocked(api.getRun).mockResolvedValue(detail)
  vi.mocked(api.uploadFile).mockReset()
})

describe('App', () => {
  it('shows the empty-state prompt on first load', async () => {
    render(<App />)
    expect(await screen.findByText(/Upload a file or pick a past run/)).toBeInTheDocument()
  })

  it('uploads a file and shows its results', async () => {
    vi.mocked(api.uploadFile).mockResolvedValue({ run_id: 'orders_sample_1', summary: detail.summary })
    render(<App />)

    const input = screen.getByLabelText(/Orders file/)
    await userEvent.upload(input, new File(['order_id'], 'orders_sample.csv', { type: 'text/csv' }))
    await userEvent.click(screen.getByRole('button', { name: 'Run automation' }))

    expect(await screen.findByText('Results: orders_sample.csv')).toBeInTheDocument()
    expect(api.getRun).toHaveBeenCalledWith('orders_sample_1')
    expect(screen.getByRole('cell', { name: 'ORD-1001' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Cleaned CSV' })).toHaveAttribute(
      'href',
      '/api/runs/orders_sample_1/files/cleaned',
    )
  })

  it('switches to the rejected tab', async () => {
    vi.mocked(api.listRuns).mockResolvedValue([{ run_id: 'orders_sample_1', ...detail.summary }])
    render(<App />)
    await userEvent.click(await screen.findByRole('button', { name: /orders_sample\.csv/ }))
    await screen.findByText('Results: orders_sample.csv')

    await userEvent.click(screen.getByRole('tab', { name: /Rejected/ }))
    expect(screen.getByRole('cell', { name: 'invalid amount' })).toBeInTheDocument()
  })

  it('shows the server error when an upload is rejected', async () => {
    vi.mocked(api.uploadFile).mockRejectedValue(new api.ApiError('Missing required columns: amount.', 400))
    render(<App />)

    await userEvent.upload(screen.getByLabelText(/Orders file/), new File(['x'], 'bad.csv'))
    await userEvent.click(screen.getByRole('button', { name: 'Run automation' }))

    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent('Missing required columns: amount.'),
    )
  })
})

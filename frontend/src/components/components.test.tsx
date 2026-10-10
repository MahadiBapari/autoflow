import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import RecordsTable from './RecordsTable'
import RunHistory from './RunHistory'
import SummaryCards from './SummaryCards'

describe('SummaryCards', () => {
  it('shows each count with its label', () => {
    render(
      <SummaryCards
        summary={{ total_records: 20, valid_records: 9, rejected_records: 11, duplicates_detected: 3 }}
      />,
    )
    expect(screen.getByText('20')).toBeInTheDocument()
    expect(screen.getByText('Valid records')).toBeInTheDocument()
    expect(screen.getByText('11')).toBeInTheDocument()
    expect(screen.getByText('Duplicates detected')).toBeInTheDocument()
  })
})

describe('RecordsTable', () => {
  it('renders headers from the first row and one body row per record', () => {
    render(
      <RecordsTable
        rows={[
          { order_id: 'ORD-1', amount: '10.00' },
          { order_id: 'ORD-2', amount: '5.50' },
        ]}
        emptyText="none"
      />,
    )
    expect(screen.getByRole('columnheader', { name: 'order_id' })).toBeInTheDocument()
    expect(screen.getByRole('cell', { name: 'ORD-2' })).toBeInTheDocument()
    expect(screen.getAllByRole('row')).toHaveLength(3) // header + 2 body rows
  })

  it('shows the empty message when there are no rows', () => {
    render(<RecordsTable rows={[]} emptyText="No valid records in this run." />)
    expect(screen.getByText('No valid records in this run.')).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })
})

describe('RunHistory', () => {
  const runs = [
    {
      run_id: 'run_a',
      input_file: 'orders.csv',
      processed_at: '2024-03-01T10:00:00',
      total_records: 2,
      valid_records: 1,
      rejected_records: 1,
      duplicates_detected: 0,
    },
  ]

  it('calls onSelect with the run id when clicked', async () => {
    const onSelect = vi.fn()
    const { default: userEvent } = await import('@testing-library/user-event')
    render(<RunHistory runs={runs} activeId={null} onSelect={onSelect} />)
    await userEvent.click(screen.getByRole('button', { name: /orders\.csv/ }))
    expect(onSelect).toHaveBeenCalledWith('run_a')
  })

  it('marks the active run', () => {
    render(<RunHistory runs={runs} activeId="run_a" onSelect={() => {}} />)
    expect(screen.getByRole('button', { name: /orders\.csv/ })).toHaveClass('active')
  })

  it('shows a placeholder when there is no history', () => {
    render(<RunHistory runs={[]} activeId={null} onSelect={() => {}} />)
    expect(screen.getByText('No runs yet.')).toBeInTheDocument()
  })
})

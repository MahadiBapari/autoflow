import type { RunSummary } from '../types'

export default function SummaryCards({ summary }: { summary: RunSummary }) {
  const cards: Array<[string, number]> = [
    ['Total records', summary.total_records],
    ['Valid records', summary.valid_records],
    ['Rejected records', summary.rejected_records],
    ['Duplicates detected', summary.duplicates_detected],
  ]
  return (
    <div className="cards">
      {cards.map(([label, value]) => (
        <div className="card" key={label}>
          <span className="card-value">{value}</span>
          <span className="card-label">{label}</span>
        </div>
      ))}
    </div>
  )
}

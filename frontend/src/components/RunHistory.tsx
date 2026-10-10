import type { RunListItem } from '../types'

interface Props {
  runs: RunListItem[]
  activeId: string | null
  onSelect: (runId: string) => void
}

export default function RunHistory({ runs, activeId, onSelect }: Props) {
  if (runs.length === 0) return <p className="muted">No runs yet.</p>
  return (
    <ul className="history">
      {runs.map((run) => (
        <li key={run.run_id}>
          <button
            type="button"
            className={run.run_id === activeId ? 'history-item active' : 'history-item'}
            onClick={() => onSelect(run.run_id)}
          >
            <span className="history-name">{run.input_file ?? run.run_id}</span>
            <span className="history-meta">
              {run.valid_records} valid · {run.rejected_records} rejected
            </span>
            {run.processed_at && <span className="history-meta">{run.processed_at.replace('T', ' ')}</span>}
          </button>
        </li>
      ))}
    </ul>
  )
}

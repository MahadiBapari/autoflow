import type { Row } from '../types'

interface Props {
  rows: Row[]
  emptyText: string
}

export default function RecordsTable({ rows, emptyText }: Props) {
  if (rows.length === 0) return <p className="muted">{emptyText}</p>

  const columns = Object.keys(rows[0])
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col}>{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {columns.map((col) => (
                <td key={col}>{row[col]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

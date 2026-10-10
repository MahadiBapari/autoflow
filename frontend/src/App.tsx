import { useCallback, useEffect, useState } from 'react'
import { getRun, listRuns, reportUrl } from './api'
import RecordsTable from './components/RecordsTable'
import RunHistory from './components/RunHistory'
import SummaryCards from './components/SummaryCards'
import UploadForm from './components/UploadForm'
import type { RunDetail, RunListItem, UploadResult } from './types'

type Tab = 'cleaned' | 'rejected'

export default function App() {
  const [runs, setRuns] = useState<RunListItem[]>([])
  const [activeRun, setActiveRun] = useState<RunDetail | null>(null)
  const [tab, setTab] = useState<Tab>('cleaned')
  const [loadingRun, setLoadingRun] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refreshRuns = useCallback(async () => {
    try {
      setRuns(await listRuns())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load run history.')
    }
  }, [])

  const selectRun = useCallback(async (runId: string) => {
    setLoadingRun(true)
    setError(null)
    try {
      setActiveRun(await getRun(runId))
      setTab('cleaned')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not open that run.')
    } finally {
      setLoadingRun(false)
    }
  }, [])

  useEffect(() => {
    refreshRuns()
  }, [refreshRuns])

  async function handleUploaded(result: UploadResult) {
    await refreshRuns()
    await selectRun(result.run_id)
  }

  const rows = activeRun ? activeRun[tab] : []

  return (
    <div className="app">
      <header className="app-header">
        <h1>AutoFlow</h1>
        <p className="muted">Validate, clean and report on business order files.</p>
      </header>

      <div className="layout">
        <aside className="sidebar">
          <section>
            <h2>New run</h2>
            <UploadForm onUploaded={handleUploaded} />
          </section>
          <section>
            <h2>History</h2>
            <RunHistory
              runs={runs}
              activeId={activeRun?.run_id ?? null}
              onSelect={selectRun}
            />
          </section>
        </aside>

        <main className="content">
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          {loadingRun && <p className="muted">Loading run…</p>}

          {!activeRun && !loadingRun && (
            <p className="muted">Upload a file or pick a past run to see its results.</p>
          )}

          {activeRun && !loadingRun && (
            <>
              <h2>Results: {activeRun.summary.input_file ?? activeRun.run_id}</h2>
              <SummaryCards summary={activeRun.summary} />

              <div className="downloads">
                <a href={reportUrl(activeRun.run_id, 'cleaned')} download>
                  Cleaned CSV
                </a>
                <a href={reportUrl(activeRun.run_id, 'rejected')} download>
                  Rejected CSV
                </a>
                <a href={reportUrl(activeRun.run_id, 'summary')} download>
                  Summary JSON
                </a>
                <a href={reportUrl(activeRun.run_id, 'input')} download>
                  Original input
                </a>
              </div>

              <div className="tabs" role="tablist">
                <button
                  role="tab"
                  aria-selected={tab === 'cleaned'}
                  className={tab === 'cleaned' ? 'tab active' : 'tab'}
                  onClick={() => setTab('cleaned')}
                >
                  Cleaned ({activeRun.summary.valid_records})
                </button>
                <button
                  role="tab"
                  aria-selected={tab === 'rejected'}
                  className={tab === 'rejected' ? 'tab active' : 'tab'}
                  onClick={() => setTab('rejected')}
                >
                  Rejected ({activeRun.summary.rejected_records})
                </button>
              </div>

              <RecordsTable
                rows={rows}
                emptyText={tab === 'cleaned' ? 'No valid records in this run.' : 'No rejected records. Nice.'}
              />
            </>
          )}
        </main>
      </div>
    </div>
  )
}

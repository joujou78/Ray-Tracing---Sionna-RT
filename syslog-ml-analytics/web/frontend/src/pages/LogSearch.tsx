import { FormEvent, useEffect, useState } from 'react'
import { logsApi } from '../api/logs'
import type { LogSearchFilters, LogSearchResponse } from '../types'

const DEFAULT_FILTERS: LogSearchFilters = {
  hours: 24,
  page: 1,
  page_size: 50,
}

const HOUR_OPTIONS = [
  { label: 'Last hour', value: 1 },
  { label: 'Last 24 hours', value: 24 },
  { label: 'Last 7 days', value: 24 * 7 },
  { label: 'Last 30 days', value: 24 * 30 },
]

function SeverityBadge({ severity }: { severity: string }) {
  return <span className={`badge badge-severity-${severity.toLowerCase()}`}>{severity}</span>
}

export function LogSearch() {
  // `form` is what the inputs show; `filters` is what was last actually
  // searched for -- kept separate so typing doesn't refire a query per
  // keystroke, only on submit or a page change.
  const [form, setForm] = useState<LogSearchFilters>(DEFAULT_FILTERS)
  const [filters, setFilters] = useState<LogSearchFilters>(DEFAULT_FILTERS)
  const [result, setResult] = useState<LogSearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    logsApi
      .search(filters)
      .then(setResult)
      .catch(() => setError('Could not search logs — is ClickHouse reachable from the API?'))
      .finally(() => setLoading(false))
  }, [filters])

  const runSearch = (e: FormEvent) => {
    e.preventDefault()
    setFilters({ ...form, page: 1 })
  }

  const goToPage = (page: number) => setFilters((f) => ({ ...f, page }))

  const totalPages = result ? Math.max(1, Math.ceil(result.total / result.page_size)) : 1

  return (
    <div>
      <h2>Log search</h2>
      <p className="page-hint">
        Filterable, paginated view over recent events in ClickHouse. Text filters (hostname, program, message) are
        substring matches; everything else is exact.
      </p>

      <form className="credential-form" onSubmit={runSearch}>
        <div className="form-grid">
          <label>
            Time range
            <select
              value={form.hours}
              onChange={(e) => setForm({ ...form, hours: Number(e.target.value) })}
            >
              {HOUR_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Message contains
            <input value={form.q ?? ''} onChange={(e) => setForm({ ...form, q: e.target.value })} placeholder="e.g. link down" />
          </label>
          <label>
            Hostname contains
            <input value={form.hostname ?? ''} onChange={(e) => setForm({ ...form, hostname: e.target.value })} />
          </label>
          <label>
            Source IP
            <input value={form.source_ip ?? ''} onChange={(e) => setForm({ ...form, source_ip: e.target.value })} placeholder="10.10.1.5" />
          </label>
          <label>
            Program contains
            <input value={form.program ?? ''} onChange={(e) => setForm({ ...form, program: e.target.value })} />
          </label>
          <label>
            Severity
            <select value={form.severity ?? ''} onChange={(e) => setForm({ ...form, severity: e.target.value || undefined })}>
              <option value="">Any</option>
              <option value="emergency">emergency</option>
              <option value="alert">alert</option>
              <option value="critical">critical</option>
              <option value="error">error</option>
              <option value="warning">warning</option>
              <option value="notice">notice</option>
              <option value="info">info</option>
              <option value="debug">debug</option>
            </select>
          </label>
          <label>
            Predicted category
            <input
              value={form.predicted_category ?? ''}
              onChange={(e) => setForm({ ...form, predicted_category: e.target.value || undefined })}
            />
          </label>
          <label>
            Anomalies only
            <select
              value={form.is_anomaly === undefined ? '' : String(form.is_anomaly)}
              onChange={(e) => setForm({ ...form, is_anomaly: e.target.value === '' ? undefined : e.target.value === 'true' })}
            >
              <option value="">Any</option>
              <option value="true">Anomalies only</option>
              <option value="false">Non-anomalies only</option>
            </select>
          </label>
        </div>
        <div className="form-actions">
          <button type="submit">Search</button>
        </div>
      </form>

      {error && <p className="form-error">{error}</p>}

      {result && (
        <p className="page-hint">
          {result.total.toLocaleString()} matching event{result.total === 1 ? '' : 's'} — page {result.page} of {totalPages}
        </p>
      )}

      <table className="data-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Hostname</th>
            <th>Source IP</th>
            <th>Severity</th>
            <th>Program</th>
            <th>Category</th>
            <th>Message</th>
          </tr>
        </thead>
        <tbody>
          {result?.items.map((ev, i) => (
            <tr key={`${ev.source_ip}-${ev.event_time}-${i}`}>
              <td className="mono">{new Date(ev.event_time).toLocaleString()}</td>
              <td>{ev.hostname}</td>
              <td className="mono">{ev.source_ip}</td>
              <td>
                <SeverityBadge severity={ev.severity} />
              </td>
              <td>{ev.program}</td>
              <td>
                {ev.predicted_category}
                {ev.is_anomaly ? <span className="badge badge-anomaly">anomaly</span> : null}
              </td>
              <td className="log-message">{ev.message}</td>
            </tr>
          ))}
          {result?.items.length === 0 && !loading && (
            <tr>
              <td colSpan={7}>No events match these filters.</td>
            </tr>
          )}
        </tbody>
      </table>

      {result && totalPages > 1 && (
        <div className="form-actions pagination">
          <button type="button" disabled={result.page <= 1} onClick={() => goToPage(result.page - 1)}>
            Previous
          </button>
          <button type="button" disabled={result.page >= totalPages} onClick={() => goToPage(result.page + 1)}>
            Next
          </button>
        </div>
      )}
    </div>
  )
}

import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, fileUrl } from '../api'
import { Alert, StatusBadge } from '../components/common'
import { DECISIONS, DOC_TYPES, formatDate, formatSize, statusLabel } from '../labels'

const FILTERS = [
  ['pending', 'Pending'],
  ['needs_more_info', 'Needs more info'],
  ['verified', 'Verified'],
  ['rejected', 'Rejected'],
  ['all', 'All'],
]

function Confidence({ value }) {
  if (value === null || value === undefined) return <span className="muted small">not yet</span>
  const tone = value >= 70 ? 'ok' : value >= 50 ? 'warn' : 'bad'
  return (
    <span className={`conf conf-${tone}`}>
      <span style={{ width: `${value}%` }} />
      {Math.round(value)}
    </span>
  )
}

export function ReviewDashboard() {
  const [status, setStatus] = useState('pending')
  const [sort, setSort] = useState('date_desc')
  const [q, setQ] = useState('')
  const [rows, setRows] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    const params = new URLSearchParams({ status, sort })
    if (q.trim()) params.set('q', q.trim())
    const t = setTimeout(() => {
      api(`/review/documents?${params}`)
        .then(setRows)
        .catch((e) => setError(e.message))
    }, 200)
    return () => clearTimeout(t)
  }, [status, sort, q])

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Review queue</h1>
          <p className="muted">Uncertain cases first: sort by confidence, lowest first.</p>
        </div>
      </div>
      <div className="toolbar">
        <div className="segmented" role="tablist">
          {FILTERS.map(([k, label]) => (
            <button key={k} className={status === k ? 'active' : ''} onClick={() => setStatus(k)}>
              {label}
            </button>
          ))}
        </div>
        <input
          className="search"
          placeholder="Search applicant name or email"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Sort">
          <option value="date_desc">Newest first</option>
          <option value="date_asc">Oldest first</option>
          <option value="confidence_asc">Confidence: lowest first</option>
          <option value="confidence_desc">Confidence: highest first</option>
        </select>
      </div>
      <Alert>{error}</Alert>
      <div className="card table-card">
        <table>
          <thead>
            <tr>
              <th>Applicant</th>
              <th>Document</th>
              <th>Uploaded</th>
              <th>AI recommendation</th>
              <th>Confidence</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>
                  <Link to={`/review/${r.id}`}>{r.owner_name}</Link>
                  <div className="muted small">{r.owner_email}</div>
                </td>
                <td>
                  {DOC_TYPES[r.doc_type]}
                  {r.version > 1 && <span className="muted small"> · v{r.version}</span>}
                </td>
                <td className="nowrap">{formatDate(r.created_at)}</td>
                <td>{r.ai_recommendation ? statusLabel(r.ai_recommendation) : <span className="muted small">Phase 3</span>}</td>
                <td>
                  <Confidence value={r.ai_confidence} />
                </td>
                <td>
                  <StatusBadge status={r.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && <p className="empty">No documents match this filter.</p>}
      </div>
    </>
  )
}

function DocumentPreview({ doc }) {
  const [url, setUrl] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => {
    let current
    fileUrl(doc.id)
      .then((u) => {
        current = u
        setUrl(u)
      })
      .catch((e) => setError(e.message))
    return () => current && URL.revokeObjectURL(current)
  }, [doc.id])
  if (error) return <Alert>{error}</Alert>
  if (!url) return <p className="muted center">Loading document…</p>
  return doc.content_type === 'application/pdf' ? (
    <iframe title="Original document" src={url} className="preview" />
  ) : (
    <img alt="Original document" src={url} className="preview" />
  )
}

function DecisionForm({ doc, onSaved }) {
  const [decision, setDecision] = useState(doc.ai_recommendation || 'verified')
  const [comment, setComment] = useState('')
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const overrides = doc.ai_recommendation && doc.ai_recommendation !== decision
  const needsComment = decision !== 'verified' || overrides

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setSaved('')
    if (needsComment && !comment.trim()) return setError('Please add a comment for the applicant.')
    try {
      await api(`/review/documents/${doc.id}/decision`, {
        method: 'POST',
        body: { decision, comment: comment.trim() || null },
      })
      setComment('')
      setSaved('Decision saved. The applicant can now see the new status.')
      onSaved()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <form className="form" onSubmit={submit}>
      <div className="segmented full">
        {Object.entries(DECISIONS).map(([k, label]) => (
          <button type="button" key={k} className={decision === k ? `active d-${k}` : ''} onClick={() => setDecision(k)}>
            {label}
          </button>
        ))}
      </div>
      {overrides && <p className="note">You are overriding the AI recommendation. Please explain why.</p>}
      <label>
        Comment {needsComment ? <small>(required, shown to the applicant)</small> : <small>(optional)</small>}
        <textarea rows={3} value={comment} onChange={(e) => setComment(e.target.value)} />
      </label>
      <Alert>{error}</Alert>
      <Alert kind="ok">{saved}</Alert>
      <button className="btn btn-primary">Save final decision</button>
    </form>
  )
}

export function ReviewDetail() {
  const { id } = useParams()
  const [doc, setDoc] = useState(null)
  const [error, setError] = useState('')
  const load = () =>
    api(`/review/documents/${id}`)
      .then(setDoc)
      .catch((e) => setError(e.message))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => void load(), [id])

  if (error) return <Alert>{error}</Alert>
  if (!doc) return <p className="muted center">Loading…</p>

  return (
    <>
      <div className="page-head">
        <div>
          <Link to="/review" className="small">
            ← Back to queue
          </Link>
          <h1>
            {DOC_TYPES[doc.doc_type]} · {doc.owner_name}
          </h1>
          <p className="muted">
            {doc.owner_email} · {doc.original_filename} · {formatSize(doc.size_bytes)} · version{' '}
            {doc.version} · uploaded {formatDate(doc.created_at)}
          </p>
        </div>
        <StatusBadge status={doc.status} />
      </div>

      <div className="split">
        <div className="card preview-card">
          <DocumentPreview doc={doc} />
        </div>
        <div className="stack">
          <div className="card">
            <h2>AI verification report</h2>
            {doc.ai_report ? (
              <pre className="report">{JSON.stringify(doc.ai_report, null, 2)}</pre>
            ) : (
              <div className="placeholder">
                <p>
                  <b>No AI report yet.</b>
                </p>
                <p className="muted small">
                  Extracted fields, the recommendation (Verified / Needs Review / Rejected), a confidence
                  score and cited sources appear here once the AI service is connected in Phase 3.
                </p>
              </div>
            )}
          </div>
          <div className="card">
            <h2>Final decision</h2>
            {doc.is_current ? (
              <DecisionForm doc={doc} onSaved={load} />
            ) : (
              <p className="muted">A newer version of this document exists.</p>
            )}
          </div>
          {doc.reviews.length > 0 && (
            <div className="card">
              <h2>Decision history</h2>
              <ul className="timeline">
                {doc.reviews.map((r) => (
                  <li key={r.id}>
                    <b>{DECISIONS[r.decision]}</b>
                    <span className="muted small">
                      {' '}
                      · reviewer #{r.reviewer_id ?? '–'} · {formatDate(r.created_at)}
                      {r.ai_recommendation && ` · AI: ${statusLabel(r.ai_recommendation)}`}
                    </span>
                    {r.comment && <p>{r.comment}</p>}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {doc.history.length > 0 && (
            <div className="card">
              <h2>Earlier versions</h2>
              <ul className="timeline">
                {doc.history.map((h) => (
                  <li key={h.id}>
                    <Link to={`/review/${h.id}`}>Version {h.version}</Link>{' '}
                    <span className="muted small">
                      {h.original_filename} · {statusLabel(h.status)} · {formatDate(h.created_at)}
                    </span>
                    {h.reviewer_comment && <p>{h.reviewer_comment}</p>}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </>
  )
}

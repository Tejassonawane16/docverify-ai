import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'
import { Alert, StatusBadge } from '../components/common'
import { DOC_TYPES, formatDate, formatSize } from '../labels'

const ACCEPT = '.pdf,.jpg,.jpeg,.png'
const MAX_MB = 10

function checkFile(file) {
  if (!file) return 'Choose a file first.'
  if (!/\.(pdf|jpe?g|png)$/i.test(file.name)) return 'Only PDF, JPG and PNG files are allowed.'
  if (file.size > MAX_MB * 1024 * 1024) return `The file is larger than ${MAX_MB} MB.`
  return ''
}

function UploadForm({ onUploaded }) {
  const [docType, setDocType] = useState('degree_certificate')
  const [file, setFile] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const input = useRef(null)

  const submit = async (e) => {
    e.preventDefault()
    const problem = checkFile(file)
    if (problem) return setError(problem)
    setError('')
    setBusy(true)
    const form = new FormData()
    form.append('doc_type', docType)
    form.append('file', file)
    try {
      await api('/documents', { method: 'POST', form })
      setFile(null)
      if (input.current) input.current.value = ''
      onUploaded()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="card upload" onSubmit={submit}>
      <h2>Upload a document</h2>
      <p className="muted small">PDF, JPG or PNG, up to {MAX_MB} MB.</p>
      <div className="upload-row">
        <label>
          Document type
          <select value={docType} onChange={(e) => setDocType(e.target.value)}>
            {Object.entries(DOC_TYPES).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </label>
        <label className="grow">
          File
          <input
            ref={input}
            type="file"
            accept={ACCEPT}
            onChange={(e) => setFile(e.target.files[0] || null)}
          />
        </label>
        <button className="btn btn-primary" disabled={busy}>
          {busy ? 'Uploading…' : 'Upload'}
        </button>
      </div>
      <Alert>{error}</Alert>
    </form>
  )
}

function ReuploadButton({ doc, onDone }) {
  const input = useRef(null)
  const [error, setError] = useState('')
  const pick = async (e) => {
    const file = e.target.files[0]
    const problem = checkFile(file)
    if (problem) return setError(problem)
    const form = new FormData()
    form.append('file', file)
    try {
      await api(`/documents/${doc.id}/versions`, { method: 'POST', form })
      onDone()
    } catch (err) {
      setError(err.message)
    }
  }
  return (
    <>
      <input ref={input} type="file" accept={ACCEPT} hidden onChange={pick} />
      <button className="btn btn-small" onClick={() => input.current.click()}>
        Upload corrected version
      </button>
      <Alert>{error}</Alert>
    </>
  )
}

export default function MyDocuments() {
  const { forget } = useAuth()
  const navigate = useNavigate()
  const [docs, setDocs] = useState([])
  const [history, setHistory] = useState(false)
  const [error, setError] = useState('')
  const [confirmDelete, setConfirmDelete] = useState('')

  const load = useCallback(() => {
    api(`/documents${history ? '?include_history=true' : ''}`)
      .then(setDocs)
      .catch((e) => setError(e.message))
  }, [history])

  useEffect(load, [load])

  const deleteAccount = async () => {
    try {
      await api('/auth/me', { method: 'DELETE' })
      forget()
      navigate('/login')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>My documents</h1>
          <p className="muted">Upload your documents and follow the status of each one.</p>
        </div>
      </div>
      <UploadForm onUploaded={load} />
      <Alert>{error}</Alert>

      <div className="card">
        <div className="card-head">
          <h2>Submitted documents</h2>
          <label className="check">
            <input type="checkbox" checked={history} onChange={(e) => setHistory(e.target.checked)} />
            Show earlier versions
          </label>
        </div>
        {docs.length === 0 ? (
          <p className="empty">No documents yet. Start by uploading your degree certificate.</p>
        ) : (
          <ul className="doc-list">
            {docs.map((d) => (
              <li key={d.id} className={d.is_current ? '' : 'old'}>
                <div className="doc-main">
                  <strong>{DOC_TYPES[d.doc_type]}</strong>
                  <span className="muted small">
                    {d.original_filename} · {formatSize(d.size_bytes)} · version {d.version} ·{' '}
                    {formatDate(d.created_at)}
                  </span>
                  {d.reviewer_comment && d.is_current && (
                    <p className="comment">
                      <b>Message from the admissions office:</b> {d.reviewer_comment}
                    </p>
                  )}
                </div>
                <div className="doc-side">
                  {d.is_current ? <StatusBadge status={d.status} /> : <span className="muted small">Replaced</span>}
                  {d.is_current && ['needs_more_info', 'rejected'].includes(d.status) && (
                    <ReuploadButton doc={d} onDone={load} />
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="card danger-zone">
        <h2>Delete my account</h2>
        <p className="muted small">
          This permanently deletes your account, all uploaded files and extracted data.
        </p>
        <div className="upload-row">
          <label className="grow">
            Type DELETE to confirm
            <input value={confirmDelete} onChange={(e) => setConfirmDelete(e.target.value)} />
          </label>
          <button className="btn btn-danger" disabled={confirmDelete !== 'DELETE'} onClick={deleteAccount}>
            Delete account
          </button>
        </div>
      </div>
    </>
  )
}

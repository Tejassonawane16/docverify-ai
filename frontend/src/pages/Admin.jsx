import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import { Alert } from '../components/common'
import { ROLES, formatDate, statusLabel } from '../labels'

function Stats() {
  const [s, setS] = useState(null)
  useEffect(() => {
    api('/admin/stats').then(setS).catch(() => {})
  }, [])
  if (!s) return null
  const docs = Object.values(s.documents_by_status).reduce((a, b) => a + b, 0)
  const tiles = [
    ['Applicants', s.users_by_role.applicant ?? 0],
    ['Reviewers', s.users_by_role.reviewer ?? 0],
    ['Documents', docs],
    ['Decisions', s.reviews_total],
  ]
  return (
    <div className="tiles">
      {tiles.map(([label, n]) => (
        <div className="tile" key={label}>
          <span>{label}</span>
          <b>{n}</b>
        </div>
      ))}
      <div className="tile wide">
        <span>Documents by status</span>
        <p className="small">
          {Object.entries(s.documents_by_status)
            .map(([k, v]) => `${statusLabel(k)}: ${v}`)
            .join(' · ') || 'none yet'}
        </p>
      </div>
    </div>
  )
}

function CreateUser({ onCreated }) {
  const empty = { full_name: '', email: '', password: '', role: 'reviewer' }
  const [form, setForm] = useState(empty)
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })
  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setOk('')
    try {
      const u = await api('/admin/users', { method: 'POST', body: form })
      setOk(`${u.full_name} can now log in as ${ROLES[u.role]}.`)
      setForm(empty)
      onCreated()
    } catch (err) {
      setError(err.message)
    }
  }
  return (
    <form className="card" onSubmit={submit}>
      <h2>Create staff account</h2>
      <div className="grid-form">
        <label>
          Full name
          <input value={form.full_name} onChange={set('full_name')} required />
        </label>
        <label>
          Email
          <input type="email" value={form.email} onChange={set('email')} required />
        </label>
        <label>
          Initial password
          <input type="password" value={form.password} onChange={set('password')} required minLength={10} />
        </label>
        <label>
          Role
          <select value={form.role} onChange={set('role')}>
            <option value="reviewer">Reviewer</option>
            <option value="admin">Admin</option>
          </select>
        </label>
      </div>
      <Alert>{error}</Alert>
      <Alert kind="ok">{ok}</Alert>
      <button className="btn btn-primary">Create account</button>
    </form>
  )
}

export function AdminUsers() {
  const { user: me } = useAuth()
  const [users, setUsers] = useState([])
  const [error, setError] = useState('')
  const load = useCallback(() => {
    api('/admin/users').then(setUsers).catch((e) => setError(e.message))
  }, [])
  useEffect(load, [load])

  const update = async (id, body) => {
    setError('')
    try {
      await api(`/admin/users/${id}`, { method: 'PATCH', body })
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Users and roles</h1>
          <p className="muted">Only staff accounts can see applicants&apos; documents.</p>
        </div>
      </div>
      <Stats />
      <CreateUser onCreated={load} />
      <Alert>{error}</Alert>
      <div className="card table-card">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className={u.is_active ? '' : 'inactive'}>
                <td>{u.full_name}</td>
                <td>{u.email}</td>
                <td>
                  <select
                    value={u.role}
                    disabled={u.id === me.id}
                    onChange={(e) => update(u.id, { role: e.target.value })}
                    aria-label={`Role of ${u.full_name}`}
                  >
                    {Object.entries(ROLES).map(([k, v]) => (
                      <option key={k} value={k}>
                        {v}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <button
                    className="btn btn-small"
                    disabled={u.id === me.id}
                    onClick={() => update(u.id, { is_active: !u.is_active })}
                  >
                    {u.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                </td>
                <td className="nowrap">{formatDate(u.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

const ACTIONS = [
  'login',
  'logout',
  'register',
  'document_upload',
  'document_new_version',
  'document_download',
  'review_decision',
  'user_created',
  'user_updated',
  'account_deleted',
]

export function AdminAudit() {
  const [filters, setFilters] = useState({ action: '', user_ref: '', date_from: '', date_to: '' })
  const [rows, setRows] = useState([])
  const [error, setError] = useState('')
  const set = (k) => (e) => setFilters({ ...filters, [k]: e.target.value })

  useEffect(() => {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([k, v]) => v && params.set(k, v))
    api(`/admin/audit?${params}`)
      .then(setRows)
      .catch((e) => setError(e.message))
  }, [filters])

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Audit log</h1>
          <p className="muted">Read-only record of logins, uploads, decisions and configuration changes.</p>
        </div>
      </div>
      <div className="toolbar">
        <select value={filters.action} onChange={set('action')} aria-label="Action">
          <option value="">All actions</option>
          {ACTIONS.map((a) => (
            <option key={a}>{a}</option>
          ))}
        </select>
        <input placeholder="User (e.g. user-3)" value={filters.user_ref} onChange={set('user_ref')} />
        <label className="inline">
          From <input type="date" value={filters.date_from} onChange={set('date_from')} />
        </label>
        <label className="inline">
          To <input type="date" value={filters.date_to} onChange={set('date_to')} />
        </label>
      </div>
      <Alert>{error}</Alert>
      <div className="card table-card">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>User</th>
              <th>Action</th>
              <th>Object</th>
              <th>Result</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td className="nowrap">{formatDate(r.timestamp)}</td>
                <td>{r.user_ref ?? '–'}</td>
                <td>
                  <code>{r.action}</code>
                </td>
                <td>{r.object_type ? `${r.object_type} #${r.object_id ?? ''}` : '–'}</td>
                <td>
                  <span className={`badge badge-${r.result === 'success' ? 'ok' : 'bad'}`}>{r.result}</span>
                </td>
                <td className="small">{r.details}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && <p className="empty">No entries for these filters.</p>}
      </div>
    </>
  )
}

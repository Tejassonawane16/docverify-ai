import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { Alert, Logo } from '../components/common'
import { homeFor } from '../labels'

function AuthCard({ title, subtitle, children }) {
  return (
    <div className="auth">
      <div className="auth-side">
        <Logo />
        <h2>Verify application documents in minutes, not weeks.</h2>
        <p>
          Upload your certificates once. Every document is checked against the admission rules and
          a reviewer makes the final decision.
        </p>
      </div>
      <div className="auth-main">
        <div className="card auth-card">
          <h1>{title}</h1>
          <p className="muted">{subtitle}</p>
          {children}
        </div>
      </div>
    </div>
  )
}

export function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to={homeFor(user.role)} replace />

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const u = await login(email, password)
      navigate(homeFor(u.role))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthCard title="Log in" subtitle="Applicants, reviewers and administrators">
      <form onSubmit={submit} className="form">
        <label>
          Email
          <input
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        <Alert>{error}</Alert>
        <button className="btn btn-primary" disabled={busy}>
          {busy ? 'Logging in…' : 'Log in'}
        </button>
      </form>
      <p className="muted small">
        New applicant? <Link to="/register">Create an account</Link>
      </p>
    </AuthCard>
  )
}

export function RegisterPage() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ fullName: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to={homeFor(user.role)} replace />
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    if (form.password.length < 10) return setError('Password must have at least 10 characters.')
    if (form.password !== form.confirm) return setError('Passwords do not match.')
    setBusy(true)
    try {
      await register(form.fullName, form.email, form.password)
      navigate('/documents')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthCard title="Create your account" subtitle="For applicants submitting documents">
      <form onSubmit={submit} className="form">
        <label>
          Full name
          <input value={form.fullName} onChange={set('fullName')} required minLength={2} />
        </label>
        <label>
          Email
          <input type="email" value={form.email} onChange={set('email')} required />
        </label>
        <label>
          Password <small className="muted">(at least 10 characters)</small>
          <input
            type="password"
            autoComplete="new-password"
            value={form.password}
            onChange={set('password')}
            required
          />
        </label>
        <label>
          Confirm password
          <input
            type="password"
            autoComplete="new-password"
            value={form.confirm}
            onChange={set('confirm')}
            required
          />
        </label>
        <Alert>{error}</Alert>
        <button className="btn btn-primary" disabled={busy}>
          {busy ? 'Creating account…' : 'Create account'}
        </button>
      </form>
      <p className="muted small">
        Already registered? <Link to="/login">Log in</Link>
      </p>
    </AuthCard>
  )
}

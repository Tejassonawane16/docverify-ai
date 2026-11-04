import { Navigate, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { ROLES, STATUS, homeFor } from '../labels'

export function StatusBadge({ status }) {
  const s = STATUS[status] ?? { label: status, tone: 'neutral' }
  return <span className={`badge badge-${s.tone}`}>{s.label}</span>
}

export function Alert({ kind = 'error', children }) {
  if (!children) return null
  return (
    <div className={`alert alert-${kind}`} role={kind === 'error' ? 'alert' : 'status'}>
      {children}
    </div>
  )
}

export function Logo() {
  return (
    <span className="logo">
      <svg viewBox="0 0 32 32" width="26" height="26" aria-hidden="true">
        <rect width="32" height="32" rx="7" fill="currentColor" />
        <path
          d="M9 16.5l4.5 4.5L23 11.5"
          stroke="var(--accent)"
          strokeWidth="3.2"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      DocVerify <b>AI</b>
    </span>
  )
}

// Protects routes by login and role (US-02, US-03)
export function RequireRole({ roles }) {
  const { user, loading } = useAuth()
  if (loading) return <p className="muted center">Loading…</p>
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to={homeFor(user.role)} replace />
  return <Outlet />
}

const NAV = {
  applicant: [{ to: '/documents', label: 'My documents' }],
  reviewer: [{ to: '/review', label: 'Review queue' }],
  admin: [
    { to: '/review', label: 'Review queue' },
    { to: '/admin/users', label: 'Users' },
    { to: '/admin/audit', label: 'Audit log' },
  ],
}

export function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const onLogout = async () => {
    await logout()
    navigate('/login')
  }
  return (
    <div className="shell">
      <header className="topbar">
        <Logo />
        <nav>
          {(NAV[user?.role] ?? []).map((n) => (
            <NavLink key={n.to} to={n.to}>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="who">
          <span>
            {user?.full_name} <small>{ROLES[user?.role]}</small>
          </span>
          <button className="btn btn-ghost" onClick={onLogout}>
            Log out
          </button>
        </div>
      </header>
      <main className="page">
        <Outlet />
      </main>
    </div>
  )
}

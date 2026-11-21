import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { StatusBadge, RequireRole } from './common'

vi.mock('../auth', () => ({ useAuth: vi.fn() }))
import { useAuth } from '../auth'

function renderAt(path, roles) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route element={<RequireRole roles={roles} />}>
          <Route path="/admin/users" element={<p>Admin page</p>} />
        </Route>
        <Route path="/login" element={<p>Login page</p>} />
        <Route path="/documents" element={<p>Applicant page</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('StatusBadge', () => {
  it('renders the label and tone', () => {
    render(<StatusBadge status="rejected" />)
    const badge = screen.getByText('Rejected')
    expect(badge).toHaveClass('badge-bad')
  })
})

describe('RequireRole', () => {
  it('redirects anonymous users to login', () => {
    useAuth.mockReturnValue({ user: null, loading: false })
    renderAt('/admin/users', ['admin'])
    expect(screen.getByText('Login page')).toBeInTheDocument()
  })

  it('redirects users with the wrong role to their own start page', () => {
    useAuth.mockReturnValue({ user: { role: 'applicant' }, loading: false })
    renderAt('/admin/users', ['admin'])
    expect(screen.getByText('Applicant page')).toBeInTheDocument()
  })

  it('shows the page for the right role', () => {
    useAuth.mockReturnValue({ user: { role: 'admin' }, loading: false })
    renderAt('/admin/users', ['admin'])
    expect(screen.getByText('Admin page')).toBeInTheDocument()
  })
})

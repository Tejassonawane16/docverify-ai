import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '../auth'
import { LoginPage, RegisterPage } from './AuthPages'

function renderWithAuth(ui) {
  return render(
    <MemoryRouter>
      <AuthProvider>{ui}</AuthProvider>
    </MemoryRouter>,
  )
}

afterEach(() => vi.restoreAllMocks())

describe('LoginPage', () => {
  it('shows the API error message when login fails', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Invalid email or password' }), { status: 401 }),
    )
    renderWithAuth(<LoginPage />)
    await userEvent.type(screen.getByLabelText('Email'), 'arjun@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'wrong-password')
    await userEvent.click(screen.getByRole('button', { name: 'Log in' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password')
    expect(fetch).toHaveBeenCalledWith('/api/auth/login', expect.objectContaining({ method: 'POST' }))
  })
})

describe('RegisterPage', () => {
  it('checks the password length before calling the API', async () => {
    const spy = vi.spyOn(globalThis, 'fetch')
    renderWithAuth(<RegisterPage />)
    await userEvent.type(screen.getByLabelText('Full name'), 'Arjun Mehta')
    await userEvent.type(screen.getByLabelText('Email'), 'arjun@example.com')
    await userEvent.type(screen.getByLabelText(/^Password/), 'short')
    await userEvent.type(screen.getByLabelText('Confirm password'), 'short')
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('at least 10 characters')
    expect(spy).not.toHaveBeenCalled()
  })
})

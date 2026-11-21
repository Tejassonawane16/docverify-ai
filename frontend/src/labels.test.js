import { describe, expect, it } from 'vitest'
import { formatSize, homeFor, statusLabel } from './labels'

describe('labels', () => {
  it('sends each role to its start page', () => {
    expect(homeFor('applicant')).toBe('/documents')
    expect(homeFor('reviewer')).toBe('/review')
    expect(homeFor('admin')).toBe('/admin/users')
  })

  it('shows readable status labels', () => {
    expect(statusLabel('needs_more_info')).toBe('Needs more information')
    expect(statusLabel('unknown')).toBe('unknown')
  })

  it('formats file sizes', () => {
    expect(formatSize(500)).toBe('500 B')
    expect(formatSize(2048)).toBe('2 KB')
    expect(formatSize(3 * 1024 * 1024)).toBe('3.0 MB')
  })
})

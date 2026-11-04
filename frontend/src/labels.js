export const DOC_TYPES = {
  degree_certificate: 'Degree certificate',
  transcript: 'Transcript of records',
  language_certificate: 'Language certificate',
  id_document: 'ID document',
  other: 'Other',
}

export const STATUS = {
  uploaded: { label: 'Uploaded', tone: 'neutral' },
  processing: { label: 'Processing', tone: 'info' },
  in_review: { label: 'In review', tone: 'info' },
  verified: { label: 'Verified', tone: 'ok' },
  needs_more_info: { label: 'Needs more information', tone: 'warn' },
  rejected: { label: 'Rejected', tone: 'bad' },
}

export const DECISIONS = {
  verified: 'Verified',
  needs_more_info: 'Needs more information',
  rejected: 'Rejected',
}

export const ROLES = { applicant: 'Applicant', reviewer: 'Reviewer', admin: 'Admin' }

export function statusLabel(status) {
  return STATUS[status]?.label ?? status
}

export function formatDate(iso) {
  if (!iso) return '–'
  return new Date(iso).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

// Where each role lands after login (US-02)
export function homeFor(role) {
  if (role === 'admin') return '/admin/users'
  if (role === 'reviewer') return '/review'
  return '/documents'
}

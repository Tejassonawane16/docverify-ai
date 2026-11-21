// Small wrapper around fetch that adds the JWT and turns API errors into readable messages.

const TOKEN_KEY = 'docverify_token'

export function getToken() {
  try {
    return sessionStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token) {
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token)
    else sessionStorage.removeItem(TOKEN_KEY)
  } catch {
    /* storage not available - the session simply ends on reload */
  }
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

function errorMessage(body, status) {
  const detail = body && body.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length) {
    return detail
      .map((d) => `${(d.loc || []).slice(-1)[0] || 'field'}: ${d.msg}`)
      .join('; ')
  }
  return `Request failed (${status})`
}

export async function api(path, { method = 'GET', body, form, raw } = {}) {
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  let payload
  if (form) payload = form
  else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  const res = await fetch(`/api${path}`, { method, headers, body: payload })
  if (res.status === 401 && token && path !== '/auth/login') {
    setToken(null)
    window.dispatchEvent(new Event('docverify:logout'))
  }
  if (!res.ok) {
    let data = null
    try {
      data = await res.json()
    } catch {
      /* no JSON body */
    }
    throw new ApiError(errorMessage(data, res.status), res.status)
  }
  if (raw) return res
  if (res.status === 204) return null
  return res.json()
}

// Fetch a protected file and return an object URL that can be shown in an <iframe>/<img>.
export async function fileUrl(docId) {
  const res = await api(`/documents/${docId}/file`, { raw: true })
  return URL.createObjectURL(await res.blob())
}

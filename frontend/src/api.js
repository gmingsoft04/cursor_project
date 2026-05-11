const API_BASE = import.meta.env.VITE_API_BASE || ''

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })
  const text = await response.text()
  const data = text ? JSON.parse(text) : null
  if (!response.ok) {
    throw new Error(data?.error || `Request failed with ${response.status}`)
  }
  return data
}

export function getDashboard() {
  return request('/api/dashboard')
}

export function getLeads(limit = 100) {
  return request(`/api/leads?limit=${limit}`)
}

export function getEmailDrafts({ status = '', limit = 50 } = {}) {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  params.set('limit', limit)
  return request(`/api/email-drafts?${params.toString()}`)
}

export function getEmailDraft(id) {
  return request(`/api/email-drafts/${id}`)
}

export function generateEmailDrafts(payload) {
  return request('/api/email-drafts/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateEmailDraft(id, payload) {
  return request(`/api/email-drafts/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function approveEmailDraft(id, reviewer) {
  return request(`/api/email-drafts/${id}/approve`, {
    method: 'POST',
    body: JSON.stringify({ reviewer }),
  })
}

export function rejectEmailDraft(id, reviewer) {
  return request(`/api/email-drafts/${id}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reviewer }),
  })
}

export function sendApprovedDrafts(payload) {
  return request('/api/email-drafts/send-approved', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

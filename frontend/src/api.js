const API_BASE = import.meta.env.VITE_API_BASE || ''
const TOKEN_KEY = 'fastcharge_leads_token'

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setStoredToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
  } else {
    localStorage.removeItem(TOKEN_KEY)
  }
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(getStoredToken() ? { Authorization: `Bearer ${getStoredToken()}` } : {}),
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

export async function login(username, password) {
  const data = await request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
  setStoredToken(data.token)
  return data
}

export function logout() {
  return request('/api/auth/logout', { method: 'POST', body: JSON.stringify({}) }).finally(() => {
    setStoredToken('')
  })
}

export function getCurrentUser() {
  return request('/api/auth/me')
}

export function getDashboard() {
  return request('/api/dashboard')
}

export function getLeads(limit = 100) {
  return request(`/api/leads?limit=${limit}`)
}

export function updateLeadCrm(id, payload) {
  return request(`/api/leads/${id}/crm`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function getAuditLogs(limit = 100) {
  return request(`/api/audit-logs?limit=${limit}`)
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

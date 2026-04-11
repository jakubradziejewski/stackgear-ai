const BASE_URL = 'http://localhost:8000'

export async function fetchHardware(token, filters = {}) {
  const params = new URLSearchParams()
  if (filters.status) params.append('status', filters.status)
  if (filters.sort_by) params.append('sort_by', filters.sort_by)
  if (filters.order) params.append('order', filters.order)

  const response = await fetch(`${BASE_URL}/hardware?${params}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) throw new Error('Failed to fetch hardware')
  return response.json()
}

export async function rentHardware(token, id) {
  const response = await fetch(`${BASE_URL}/hardware/${id}/rent`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || 'Failed to rent')
  }
  return response.json()
}

export async function returnHardware(token, id) {
  const response = await fetch(`${BASE_URL}/hardware/${id}/return`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || 'Failed to return')
  }
  return response.json()
}
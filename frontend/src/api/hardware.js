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
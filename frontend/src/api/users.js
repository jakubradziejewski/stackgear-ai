const BASE_URL = 'http://localhost:8000'

export async function fetchUsers(token) {
  const response = await fetch(`${BASE_URL}/users`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) throw new Error('Failed to fetch users')
  return response.json()
}

export async function createUser(token, payload) {
  const response = await fetch(`${BASE_URL}/users`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
  const data = await response.json()
  if (!response.ok) throw new Error(data.detail || 'Failed to create user')
  return data
}

export async function deleteUser(token, id) {
  const response = await fetch(`${BASE_URL}/users/${id}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || 'Failed to delete user')
  }
}
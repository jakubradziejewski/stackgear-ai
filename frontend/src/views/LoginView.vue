<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const error = ref(null)
const loading = ref(false)

async function handleLogin() {
  error.value = null
  loading.value = true

  try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value, password: password.value }),
    })

    const data = await response.json()

    if (!response.ok) {
      error.value = data.detail || 'Login failed'
      return
    }

    const payload = JSON.parse(atob(data.access_token.split('.')[1]))
    authStore.setAuth(data.access_token, {
      id: payload.user_id,
      email: payload.email,
      is_admin: payload.is_admin,
    })

    router.push('/dashboard')
  } catch {
    error.value = 'Could not reach the server'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="card login-box">
      <h1>Hardware Hub</h1>
      <p class="login-subtitle">Sign in to access your inventory workspace</p>

      <form @submit.prevent="handleLogin">
        <div class="field">
          <label>Email</label>
          <input
            v-model="email"
            class="control"
            type="email"
            placeholder="admin@stackgear.com"
            required
            autofocus
          />
        </div>

        <div class="field mt-075">
          <label>Password</label>
          <input
            v-model="password"
            class="control"
            type="password"
            placeholder="********"
            required
          />
        </div>

        <p v-if="error" class="alert-error mt-08">{{ error }}</p>

        <button class="btn btn-primary mt-06 w-full" type="submit" :disabled="loading">
          {{ loading ? 'Signing in...' : 'Sign in' }}
        </button>
      </form>
    </div>
  </div>
</template>

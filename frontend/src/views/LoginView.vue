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
    const response = await fetch('http://localhost:8000/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value, password: password.value }),
    })

    const data = await response.json()

    if (!response.ok) {
      error.value = data.detail || 'Login failed'
      return
    }

    // FastAPI returns { access_token, token_type }
    // We decode the token to get user info for now
    const payload = JSON.parse(atob(data.access_token.split('.')[1]))
    authStore.setAuth(data.access_token, {
      email: payload.email,
      is_admin: payload.is_admin,
    })

    router.push('/dashboard')
  } catch (e) {
    error.value = 'Could not reach the server'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrapper">
    <div class="login-box">
      <h1>Hardware Hub</h1>
      <p class="subtitle">Sign in to continue</p>

      <form @submit.prevent="handleLogin">
        <div class="field">
          <label>Email</label>
          <input
            v-model="email"
            type="email"
            placeholder="admin@stackgear.com"
            required
            autofocus
          />
        </div>

        <div class="field">
          <label>Password</label>
          <input
            v-model="password"
            type="password"
            placeholder="••••••••"
            required
          />
        </div>

        <p v-if="error" class="error">{{ error }}</p>

        <button type="submit" :disabled="loading">
          {{ loading ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
}
.login-box {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  width: 100%;
  max-width: 360px;
}
h1 {
  margin: 0 0 4px;
  font-size: 1.5rem;
}
.subtitle {
  color: #666;
  margin: 0 0 1.5rem;
  font-size: 0.9rem;
}
.field {
  margin-bottom: 1rem;
}
label {
  display: block;
  font-size: 0.85rem;
  font-weight: 500;
  margin-bottom: 4px;
}
input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  box-sizing: border-box;
}
input:focus {
  outline: none;
  border-color: #555;
}
button {
  width: 100%;
  padding: 0.6rem;
  background: #111;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  margin-top: 0.5rem;
}
button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.error {
  color: #c0392b;
  font-size: 0.85rem;
  margin: 0.5rem 0;
}
</style>
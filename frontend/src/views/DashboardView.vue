<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import { fetchHardware } from '../api/hardware'

const authStore = useAuthStore()
const router = useRouter()
const hardware = ref([])
const error = ref(null)

async function loadHardware() {
  try {
    hardware.value = await fetchHardware(authStore.token)
  } catch (e) {
    error.value = 'Could not load hardware'
  }
}

function logout() {
  authStore.logout()
  router.push('/')
}

onMounted(() => loadHardware())
</script>

<template>
  <div style="padding: 2rem">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem">
      <h1>Hardware Hub</h1>
      <div style="display: flex; align-items: center; gap: 1rem">
        <span style="font-size: 0.85rem; color: #666">{{ authStore.user?.email }}</span>
        <button @click="logout">Sign out</button>
      </div>
    </div>

    <p v-if="error" style="color: red">{{ error }}</p>

    <table v-if="hardware.length" style="width: 100%; border-collapse: collapse">
      <thead>
        <tr style="border-bottom: 2px solid #ddd; text-align: left">
          <th style="padding: 8px">Name</th>
          <th style="padding: 8px">Brand</th>
          <th style="padding: 8px">Purchase Date</th>
          <th style="padding: 8px">Status</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="item in hardware"
          :key="item.id"
          style="border-bottom: 1px solid #eee"
        >
          <td style="padding: 8px">{{ item.name }}</td>
          <td style="padding: 8px">{{ item.brand || '—' }}</td>
          <td style="padding: 8px">{{ item.purchase_date || '—' }}</td>
          <td style="padding: 8px">
            <span :style="{
              padding: '2px 8px',
              borderRadius: '10px',
              fontSize: '0.8rem',
              fontWeight: '500',
              background: item.status === 'available' ? '#d4edda' : item.status === 'in_use' ? '#cce5ff' : item.status === 'repair' ? '#f8d7da' : '#e2e3e5',
              color: item.status === 'available' ? '#155724' : item.status === 'in_use' ? '#004085' : item.status === 'repair' ? '#721c24' : '#383d41',
            }">{{ item.status }}</span>
          </td>
        </tr>
      </tbody>
    </table>

    <p v-else-if="!error">Loading…</p>
  </div>
</template>
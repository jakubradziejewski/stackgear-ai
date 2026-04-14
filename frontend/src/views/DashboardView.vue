<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import {
  fetchHardware,
  rentHardware,
  returnHardware,
  semanticSearchHardware,
} from '../api/hardware'
import { io } from 'socket.io-client'

const authStore = useAuthStore()
const router = useRouter()
const hardware = ref([])
const error = ref(null)
const statusFilter = ref('')
const sortBy = ref('name')
const order = ref('asc')

const semanticQuery = ref('')
const searchSummary = ref('')
const searchError = ref(null)
const searchLoading = ref(false)
const searchActive = ref(false)

async function loadHardware() {
  error.value = null
  try {
    hardware.value = await fetchHardware(authStore.token, {
      status: statusFilter.value,
      sort_by: sortBy.value,
      order: order.value,
    })
  } catch (e) {
    error.value = 'Could not load hardware'
  }
}

async function handleSemanticSearch(options = {}) {
  const query = semanticQuery.value.trim()
  if (!query) {
    if (searchActive.value) {
      await clearSemanticSearch()
      return
    }
    searchError.value = 'Type what you need to find gear.'
    searchSummary.value = ''
    searchActive.value = false
    return
  }

  searchLoading.value = true
  searchError.value = null
  error.value = null

  try {
    const result = await semanticSearchHardware(authStore.token, query)
    hardware.value = result.items
    searchSummary.value = result.summary
    searchActive.value = true
  } catch (e) {
    searchError.value = options.silent ? 'Semantic search could not refresh.' : e.message
  } finally {
    searchLoading.value = false
  }
}

async function clearSemanticSearch({ reload = true } = {}) {
  semanticQuery.value = ''
  searchSummary.value = ''
  searchError.value = null
  searchLoading.value = false
  searchActive.value = false

  if (reload) {
    await loadHardware()
  }
}

async function refreshVisibleHardware() {
  if (searchActive.value && semanticQuery.value.trim()) {
    await handleSemanticSearch({ silent: true })
    return
  }
  await loadHardware()
}

async function handleRent(id) {
  try {
    await rentHardware(authStore.token, id)
  } catch (e) {
    alert(e.message)
    await refreshVisibleHardware()
  }
}

async function handleReturn(id) {
  try {
    await returnHardware(authStore.token, id)
  } catch (e) {
    alert(e.message)
    await refreshVisibleHardware()
  }
}

async function handleTableControlsChange() {
  if (searchActive.value) {
    await clearSemanticSearch()
    return
  }
  await loadHardware()
}

function logout() {
  socket.disconnect()
  authStore.logout()
  router.push('/')
}

const socket = io({
  transports: ['websocket', 'polling'],
  path: '/socket.io',
})

socket.on('connect', () => {
  console.log('[socket] connected:', socket.id)
})

socket.on('hardware_updated', () => {
  refreshVisibleHardware()
})

socket.on('disconnect', () => {
  console.log('[socket] disconnected')
})

onMounted(() => loadHardware())

onUnmounted(() => {
  socket.disconnect()
})
</script>

<template>
  <div style="padding: 2rem; max-width: 960px; margin: 0 auto">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem">
      <h1 style="margin: 0">Hardware Hub</h1>
      <div style="display: flex; align-items: center; gap: 1rem">
        <span style="font-size: 0.85rem; color: #666">{{ authStore.user?.email }}</span>
        <button v-if="authStore.isAdmin" @click="router.push('/admin')">Admin panel</button>
        <button @click="logout">Sign out</button>
      </div>
    </div>

    <div style="display: flex; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap">
      <select v-model="statusFilter" @change="handleTableControlsChange">
        <option value="">All statuses</option>
        <option value="available">Available</option>
        <option value="in_use">In Use</option>
        <option value="repair">Repair</option>
        <option value="unknown">Unknown</option>
      </select>

      <select v-model="sortBy" @change="handleTableControlsChange">
        <option value="name">Sort by Name</option>
        <option value="purchase_date">Sort by Date</option>
        <option value="status">Sort by Status</option>
      </select>

      <select v-model="order" @change="handleTableControlsChange">
        <option value="asc">Ascending</option>
        <option value="desc">Descending</option>
      </select>

      <span style="font-size: 0.8rem; color: #999; align-self: center">
        {{ socket.connected ? 'live' : 'reconnecting...' }}
      </span>
    </div>

    <div style="display: flex; gap: 0.75rem; margin-bottom: 1rem; flex-wrap: wrap">
      <input
        v-model="semanticQuery"
        type="text"
        placeholder="Describe what you need, for example: something to record a presentation"
        style="flex: 1 1 420px; min-width: 260px; padding: 0.65rem 0.8rem"
        @keyup.enter="handleSemanticSearch"
      />
      <button
        @click="handleSemanticSearch"
        :disabled="searchLoading"
        style="padding: 0.65rem 1rem"
      >
        {{ searchLoading ? 'Searching...' : 'Search with AI' }}
      </button>
      <button
        v-if="searchActive || semanticQuery"
        @click="clearSemanticSearch"
        style="padding: 0.65rem 1rem"
      >
        Clear
      </button>
    </div>

    <p v-if="error" style="color: red">{{ error }}</p>
    <p v-if="searchError" style="color: red; margin-top: -0.25rem">{{ searchError }}</p>

    <div
      v-if="searchActive"
      style="background: #f5f7fb; border: 1px solid #dbe3f0; border-radius: 8px; padding: 0.9rem 1rem; margin-bottom: 1rem"
    >
      <div style="font-size: 0.85rem; color: #4b5563; margin-bottom: 0.35rem">
        Semantic matches for "{{ semanticQuery }}"
      </div>
      <div style="font-size: 0.95rem; color: #1f2937">
        {{ searchSummary || 'Showing the closest matching gear.' }}
      </div>
    </div>

    <table v-if="hardware.length" style="width: 100%; border-collapse: collapse">
      <thead>
        <tr style="border-bottom: 2px solid #ddd; text-align: left">
          <th style="padding: 8px">Name</th>
          <th style="padding: 8px">Brand</th>
          <th style="padding: 8px">Purchase Date</th>
          <th style="padding: 8px">Status</th>
          <th style="padding: 8px">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in hardware" :key="item.id" style="border-bottom: 1px solid #eee">
          <td style="padding: 8px">{{ item.name }}</td>
          <td style="padding: 8px">{{ item.brand || '-' }}</td>
          <td style="padding: 8px">{{ item.purchase_date || '-' }}</td>
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
          <td style="padding: 8px">
            <button
              v-if="item.status === 'available'"
              @click="handleRent(item.id)"
              style="font-size: 0.8rem; padding: 3px 10px; cursor: pointer"
            >
              Rent
            </button>
            <button
              v-else-if="item.status === 'in_use' && (authStore.isAdmin || item.rented_by_id === authStore.user?.id)"
              @click="handleReturn(item.id)"
              style="font-size: 0.8rem; padding: 3px 10px; cursor: pointer"
            >
              Return
            </button>
            <span v-else style="font-size: 0.8rem; color: #999">-</span>
          </td>
        </tr>
      </tbody>
    </table>

    <p v-else-if="!error" style="color: #666">
      {{ searchActive ? 'No semantic matches found.' : 'No items found.' }}
    </p>
  </div>
</template>

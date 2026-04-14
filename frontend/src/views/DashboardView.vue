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

const socket = io(import.meta.env.VITE_API_URL || 'http://localhost:8000', {
  transports: ['websocket', 'polling'],
  path: '/socket.io',
})

function statusClass(status) {
  return `status-pill status-${status}`
}

function statusLabel(status) {
  if (status === 'in_use') return 'In use'
  if (status === 'available') return 'Available'
  if (status === 'repair') return 'Repair'
  return 'Unknown'
}

async function loadHardware() {
  error.value = null
  try {
    hardware.value = await fetchHardware(authStore.token, {
      status: statusFilter.value,
      sort_by: sortBy.value,
      order: order.value,
    })
  } catch {
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

  if (reload) await loadHardware()
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

socket.on('hardware_updated', () => {
  refreshVisibleHardware()
})

onMounted(() => {
  loadHardware()
})

onUnmounted(() => {
  socket.disconnect()
})
</script>

<template>
  <div class="page-shell">
    <div class="page-header">
      <div class="header-title">
        <h1>Hardware Hub</h1>
        <p>Live inventory with AI-assisted semantic search</p>
      </div>
      <div class="header-actions">
        <span class="user-chip">{{ authStore.user?.email }}</span>
        <button v-if="authStore.isAdmin" class="btn" @click="router.push('/admin')">Admin panel</button>
        <button class="btn" @click="logout">Sign out</button>
      </div>
    </div>

    <div class="toolbar">
      <select v-model="statusFilter" class="control" @change="handleTableControlsChange">
        <option value="">All statuses</option>
        <option value="available">Available</option>
        <option value="in_use">In Use</option>
        <option value="repair">Repair</option>
        <option value="unknown">Unknown</option>
      </select>

      <select v-model="sortBy" class="control" @change="handleTableControlsChange">
        <option value="name">Sort by Name</option>
        <option value="purchase_date">Sort by Date</option>
        <option value="status">Sort by Status</option>
      </select>

      <select v-model="order" class="control" @change="handleTableControlsChange">
        <option value="asc">Ascending</option>
        <option value="desc">Descending</option>
      </select>

      <span class="live-dot" :class="{ 'is-live': socket.connected }">
        {{ socket.connected ? 'Live updates' : 'Reconnecting...' }}
      </span>
    </div>

    <div class="search-row">
      <input
        v-model="semanticQuery"
        class="control"
        type="text"
        placeholder="Describe what you need, for example: something to record a presentation"
        @keyup.enter="handleSemanticSearch"
      />
      <button class="btn btn-primary" :disabled="searchLoading" @click="handleSemanticSearch">
        {{ searchLoading ? 'Searching...' : 'Search with AI' }}
      </button>
      <button v-if="searchActive || semanticQuery" class="btn" @click="clearSemanticSearch">Clear</button>
    </div>

    <p v-if="error" class="alert-error">{{ error }}</p>
    <p v-if="searchError" class="alert-error">{{ searchError }}</p>

    <div v-if="searchActive" class="hint-card">
      <p>Semantic matches for "{{ semanticQuery }}"</p>
      <p>{{ searchSummary || 'Showing the closest matching gear.' }}</p>
    </div>

    <div v-if="hardware.length" class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Brand</th>
            <th>Purchase Date</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in hardware" :key="item.id">
            <td>{{ item.name }}</td>
            <td>{{ item.brand || '-' }}</td>
            <td>{{ item.purchase_date || '-' }}</td>
            <td>
              <span :class="statusClass(item.status)">{{ statusLabel(item.status) }}</span>
            </td>
            <td>
              <button
                v-if="item.status === 'available'"
                class="btn btn-primary btn-sm"
                @click="handleRent(item.id)"
              >
                Rent
              </button>
              <button
                v-else-if="item.status === 'in_use' && (authStore.isAdmin || item.rented_by_id === authStore.user?.id)"
                class="btn btn-sm"
                @click="handleReturn(item.id)"
              >
                Return
              </button>
              <span v-else class="muted">-</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-else-if="!error" class="empty-state">
      {{ searchActive ? 'No semantic matches found.' : 'No items found.' }}
    </p>
  </div>
</template>

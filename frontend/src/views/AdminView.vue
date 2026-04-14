<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import { fetchHardware, createHardware, deleteHardware, toggleRepair } from '../api/hardware'
import { fetchUsers, createUser, deleteUser } from '../api/users'
import AuditPanel from './AuditView.vue'

const authStore = useAuthStore()
const router = useRouter()

if (!authStore.isAdmin) router.push('/dashboard')

const activeTab = ref('hardware')

const hardware = ref([])
const hardwareError = ref(null)
const newHardware = ref({ name: '', brand: '', purchase_date: '', notes: '' })
const hardwareFormError = ref(null)

const users = ref([])
const usersError = ref(null)
const newUser = ref({ email: '', username: '', password: '', is_admin: false })
const userFormError = ref(null)

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
  hardwareError.value = null
  try {
    hardware.value = await fetchHardware(authStore.token)
  } catch {
    hardwareError.value = 'Could not load hardware'
  }
}

async function handleCreateHardware() {
  hardwareFormError.value = null
  try {
    await createHardware(authStore.token, {
      name: newHardware.value.name,
      brand: newHardware.value.brand || null,
      purchase_date: newHardware.value.purchase_date || null,
      notes: newHardware.value.notes || null,
    })
    newHardware.value = { name: '', brand: '', purchase_date: '', notes: '' }
    await loadHardware()
  } catch (e) {
    hardwareFormError.value = e.message
  }
}

async function handleDeleteHardware(id) {
  if (!confirm('Delete this item?')) return
  try {
    await deleteHardware(authStore.token, id)
    await loadHardware()
  } catch (e) {
    alert(e.message)
  }
}

async function handleToggleRepair(id) {
  try {
    await toggleRepair(authStore.token, id)
    await loadHardware()
  } catch (e) {
    alert(e.message)
  }
}

async function loadUsers() {
  usersError.value = null
  try {
    users.value = await fetchUsers(authStore.token)
  } catch {
    usersError.value = 'Could not load users'
  }
}

async function handleCreateUser() {
  userFormError.value = null
  try {
    await createUser(authStore.token, {
      email: newUser.value.email,
      username: newUser.value.username,
      password: newUser.value.password,
      is_admin: newUser.value.is_admin,
    })
    newUser.value = { email: '', username: '', password: '', is_admin: false }
    await loadUsers()
  } catch (e) {
    userFormError.value = e.message
  }
}

async function handleDeleteUser(id) {
  if (!confirm('Delete this user?')) return
  try {
    await deleteUser(authStore.token, id)
    await loadUsers()
  } catch (e) {
    alert(e.message)
  }
}

onMounted(() => {
  loadHardware()
  loadUsers()
})
</script>

<template>
  <div class="page-shell">
    <div class="page-header">
      <div class="header-title">
        <h1>Admin Command Center</h1>
        <p>Manage hardware, user access, and run AI audit checks</p>
      </div>
      <div class="header-actions">
        <button class="btn" @click="router.push('/dashboard')">Back to dashboard</button>
      </div>
    </div>

    <div class="tabs">
      <button class="tab-btn" :class="{ 'is-active': activeTab === 'hardware' }" @click="activeTab = 'hardware'">
        Hardware
      </button>
      <button class="tab-btn" :class="{ 'is-active': activeTab === 'users' }" @click="activeTab = 'users'">
        Users
      </button>
    </div>

    <div v-if="activeTab === 'hardware'">
      <div class="card form-card">
        <h3>Add hardware</h3>
        <div class="form-grid">
          <div class="field">
            <label>Name *</label>
            <input v-model="newHardware.name" class="control" placeholder="MacBook Pro 14" />
          </div>
          <div class="field">
            <label>Brand</label>
            <input v-model="newHardware.brand" class="control" placeholder="Apple" />
          </div>
          <div class="field">
            <label>Purchase date</label>
            <input v-model="newHardware.purchase_date" class="control" type="date" />
          </div>
          <div class="field">
            <label>Notes</label>
            <input v-model="newHardware.notes" class="control" placeholder="Optional notes" />
          </div>
        </div>
        <p v-if="hardwareFormError" class="alert-error mt-075">{{ hardwareFormError }}</p>
        <button class="btn btn-primary mt-065" :disabled="!newHardware.name" @click="handleCreateHardware">
          Add item
        </button>
      </div>

      <p v-if="hardwareError" class="alert-error">{{ hardwareError }}</p>
      <div v-if="hardware.length" class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Brand</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in hardware" :key="item.id">
              <td>{{ item.name }}</td>
              <td>{{ item.brand || '-' }}</td>
              <td><span :class="statusClass(item.status)">{{ statusLabel(item.status) }}</span></td>
              <td class="spaced-actions">
                <button
                  v-if="item.status !== 'in_use'"
                  class="btn btn-sm"
                  @click="handleToggleRepair(item.id)"
                >
                  {{ item.status === 'repair' ? 'Mark available' : 'Mark repair' }}
                </button>
                <button class="btn btn-danger btn-sm" @click="handleDeleteHardware(item.id)">
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="empty-state">No hardware found.</p>
    </div>

    <div v-if="activeTab === 'users'">
      <div class="card form-card">
        <h3>Create user</h3>
        <div class="form-grid">
          <div class="field">
            <label>Email *</label>
            <input v-model="newUser.email" class="control" type="email" placeholder="user@company.com" />
          </div>
          <div class="field">
            <label>Username *</label>
            <input v-model="newUser.username" class="control" placeholder="johndoe" />
          </div>
          <div class="field">
            <label>Password *</label>
            <input v-model="newUser.password" class="control" type="password" placeholder="********" />
          </div>
          <div class="field-checkbox">
            <input v-model="newUser.is_admin" type="checkbox" id="is_admin" />
            <label for="is_admin">Admin account</label>
          </div>
        </div>
        <p v-if="userFormError" class="alert-error mt-075">{{ userFormError }}</p>
        <button
          class="btn btn-primary mt-065"
          :disabled="!newUser.email || !newUser.username || !newUser.password"
          @click="handleCreateUser"
        >
          Create user
        </button>
      </div>

      <p v-if="usersError" class="alert-error">{{ usersError }}</p>
      <div v-if="users.length" class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Email</th>
              <th>Username</th>
              <th>Role</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>{{ user.email }}</td>
              <td>{{ user.username }}</td>
              <td>
                <span class="status-pill" :class="user.is_admin ? 'status-repair' : 'status-unknown'">
                  {{ user.is_admin ? 'Admin' : 'User' }}
                </span>
              </td>
              <td>
                <button
                  v-if="user.email !== authStore.user?.email"
                  class="btn btn-danger btn-sm"
                  @click="handleDeleteUser(user.id)"
                >
                  Delete
                </button>
                <span v-else class="muted">You</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="empty-state">No users found.</p>
    </div>

    <AuditPanel />
  </div>
</template>

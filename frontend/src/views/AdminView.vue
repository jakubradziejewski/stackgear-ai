<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import { fetchHardware, createHardware, deleteHardware, toggleRepair } from '../api/hardware'
import { fetchUsers, createUser, deleteUser } from '../api/users'
import AuditPanel from './AuditView.vue'
const authStore = useAuthStore()
const router = useRouter()

// Guard — non-admins get sent back to dashboard
if (!authStore.isAdmin) router.push('/dashboard')

const activeTab = ref('hardware')

// ---------------------------------------------------------------------------
// Hardware state
// ---------------------------------------------------------------------------
const hardware = ref([])
const hardwareError = ref(null)
const newHardware = ref({ name: '', brand: '', purchase_date: '', notes: '' })
const hardwareFormError = ref(null)

async function loadHardware() {
  hardwareError.value = null
  try {
    hardware.value = await fetchHardware(authStore.token)
  } catch (e) {
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

// ---------------------------------------------------------------------------
// Users state
// ---------------------------------------------------------------------------
const users = ref([])
const usersError = ref(null)
const newUser = ref({ email: '', username: '', password: '', is_admin: false })
const userFormError = ref(null)

async function loadUsers() {
  usersError.value = null
  try {
    users.value = await fetchUsers(authStore.token)
  } catch (e) {
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

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
onMounted(() => {
  loadHardware()
  loadUsers()
})
</script>

<template>
  <div style="padding: 2rem; max-width: 960px; margin: 0 auto">

    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem">
      <h1 style="margin: 0">Admin Panel</h1>
      <div style="display: flex; gap: 1rem">
        <button @click="router.push('/dashboard')">← Dashboard</button>
      </div>
    </div>

    <!-- Tabs -->
    <div style="display: flex; gap: 0; margin-bottom: 1.5rem; border-bottom: 2px solid #ddd">
      <button
        @click="activeTab = 'hardware'"
        :style="{
          padding: '8px 20px',
          border: 'none',
          borderBottom: activeTab === 'hardware' ? '2px solid #111' : '2px solid transparent',
          background: 'none',
          fontWeight: activeTab === 'hardware' ? '600' : '400',
          cursor: 'pointer',
          marginBottom: '-2px',
        }"
      >Hardware</button>
      <button
        @click="activeTab = 'users'"
        :style="{
          padding: '8px 20px',
          border: 'none',
          borderBottom: activeTab === 'users' ? '2px solid #111' : '2px solid transparent',
          background: 'none',
          fontWeight: activeTab === 'users' ? '600' : '400',
          cursor: 'pointer',
          marginBottom: '-2px',
        }"
      >Users</button>
    </div>

    <!-- ------------------------------------------------------------------ -->
    <!-- Hardware tab                                                         -->
    <!-- ------------------------------------------------------------------ -->
    <div v-if="activeTab === 'hardware'">

      <!-- Add hardware form -->
      <div style="background: #f9f9f9; padding: 1.25rem; border-radius: 8px; margin-bottom: 1.5rem">
        <h3 style="margin: 0 0 1rem">Add hardware</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem">
          <div>
            <label style="font-size: 0.85rem; font-weight: 500; display: block; margin-bottom: 3px">Name *</label>
            <input v-model="newHardware.name" placeholder="MacBook Pro 14" style="width: 100%; padding: 6px 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box" />
          </div>
          <div>
            <label style="font-size: 0.85rem; font-weight: 500; display: block; margin-bottom: 3px">Brand</label>
            <input v-model="newHardware.brand" placeholder="Apple" style="width: 100%; padding: 6px 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box" />
          </div>
          <div>
            <label style="font-size: 0.85rem; font-weight: 500; display: block; margin-bottom: 3px">Purchase date</label>
            <input v-model="newHardware.purchase_date" type="date" style="width: 100%; padding: 6px 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box" />
          </div>
          <div>
            <label style="font-size: 0.85rem; font-weight: 500; display: block; margin-bottom: 3px">Notes</label>
            <input v-model="newHardware.notes" placeholder="Optional notes" style="width: 100%; padding: 6px 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box" />
          </div>
        </div>
        <p v-if="hardwareFormError" style="color: red; font-size: 0.85rem; margin: 0.5rem 0 0">{{ hardwareFormError }}</p>
        <button
          @click="handleCreateHardware"
          :disabled="!newHardware.name"
          style="margin-top: 0.75rem; padding: 6px 18px; background: #111; color: white; border: none; border-radius: 6px; cursor: pointer"
        >Add item</button>
      </div>

      <!-- Hardware table -->
      <p v-if="hardwareError" style="color: red">{{ hardwareError }}</p>
      <table v-if="hardware.length" style="width: 100%; border-collapse: collapse">
        <thead>
          <tr style="border-bottom: 2px solid #ddd; text-align: left">
            <th style="padding: 8px">Name</th>
            <th style="padding: 8px">Brand</th>
            <th style="padding: 8px">Status</th>
            <th style="padding: 8px">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in hardware" :key="item.id" style="border-bottom: 1px solid #eee">
            <td style="padding: 8px">{{ item.name }}</td>
            <td style="padding: 8px">{{ item.brand || '—' }}</td>
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
            <td style="padding: 8px; display: flex; gap: 6px; flex-wrap: wrap">
              <button
                v-if="item.status !== 'in_use'"
                @click="handleToggleRepair(item.id)"
                style="font-size: 0.8rem; padding: 3px 10px; cursor: pointer"
              >
                {{ item.status === 'repair' ? 'Mark available' : 'Mark repair' }}
              </button>
              <button
                @click="handleDeleteHardware(item.id)"
                style="font-size: 0.8rem; padding: 3px 10px; cursor: pointer; background: #fee2e2; border: 1px solid #fca5a5; border-radius: 4px"
              >
                Delete
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ------------------------------------------------------------------ -->
    <!-- Users tab                                                            -->
    <!-- ------------------------------------------------------------------ -->
    <div v-if="activeTab === 'users'">

      <!-- Add user form -->
      <div style="background: #f9f9f9; padding: 1.25rem; border-radius: 8px; margin-bottom: 1.5rem">
        <h3 style="margin: 0 0 1rem">Create user</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem">
          <div>
            <label style="font-size: 0.85rem; font-weight: 500; display: block; margin-bottom: 3px">Email *</label>
            <input v-model="newUser.email" type="email" placeholder="user@company.com" style="width: 100%; padding: 6px 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box" />
          </div>
          <div>
            <label style="font-size: 0.85rem; font-weight: 500; display: block; margin-bottom: 3px">Username *</label>
            <input v-model="newUser.username" placeholder="johndoe" style="width: 100%; padding: 6px 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box" />
          </div>
          <div>
            <label style="font-size: 0.85rem; font-weight: 500; display: block; margin-bottom: 3px">Password *</label>
            <input v-model="newUser.password" type="password" placeholder="••••••••" style="width: 100%; padding: 6px 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box" />
          </div>
          <div style="display: flex; align-items: center; gap: 8px; padding-top: 1.4rem">
            <input v-model="newUser.is_admin" type="checkbox" id="is_admin" />
            <label for="is_admin" style="font-size: 0.85rem; font-weight: 500">Admin account</label>
          </div>
        </div>
        <p v-if="userFormError" style="color: red; font-size: 0.85rem; margin: 0.5rem 0 0">{{ userFormError }}</p>
        <button
          @click="handleCreateUser"
          :disabled="!newUser.email || !newUser.username || !newUser.password"
          style="margin-top: 0.75rem; padding: 6px 18px; background: #111; color: white; border: none; border-radius: 6px; cursor: pointer"
        >Create user</button>
      </div>

      <!-- Users table -->
      <p v-if="usersError" style="color: red">{{ usersError }}</p>
      <table v-if="users.length" style="width: 100%; border-collapse: collapse">
        <thead>
          <tr style="border-bottom: 2px solid #ddd; text-align: left">
            <th style="padding: 8px">Email</th>
            <th style="padding: 8px">Username</th>
            <th style="padding: 8px">Role</th>
            <th style="padding: 8px">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id" style="border-bottom: 1px solid #eee">
            <td style="padding: 8px">{{ user.email }}</td>
            <td style="padding: 8px">{{ user.username }}</td>
            <td style="padding: 8px">
              <span :style="{
                padding: '2px 8px',
                borderRadius: '10px',
                fontSize: '0.8rem',
                fontWeight: '500',
                background: user.is_admin ? '#fef3c7' : '#f3f4f6',
                color: user.is_admin ? '#92400e' : '#374151',
              }">{{ user.is_admin ? 'Admin' : 'User' }}</span>
            </td>
            <td style="padding: 8px">
              <button
                v-if="user.email !== authStore.user?.email"
                @click="handleDeleteUser(user.id)"
                style="font-size: 0.8rem; padding: 3px 10px; cursor: pointer; background: #fee2e2; border: 1px solid #fca5a5; border-radius: 4px"
              >
                Delete
              </button>
              <span v-else style="font-size: 0.8rem; color: #999">You</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
<AuditPanel />
  </div>
</template>
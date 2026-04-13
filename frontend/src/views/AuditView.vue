<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { runAudit } from '../api/hardware'

const authStore = useAuthStore()
const findings = ref([])
const summary = ref('')
const loading = ref(false)
const error = ref(null)
const ran = ref(false)

async function handleAudit() {
  loading.value = true
  error.value = null
  findings.value = []
  summary.value = ''

  try {
    const result = await runAudit(authStore.token)
    findings.value = result.findings
    summary.value = result.summary
    ran.value = true
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function severityStyle(severity) {
  if (severity === 'error')   return { background: '#fee2e2', color: '#991b1b', border: '1px solid #fca5a5' }
  if (severity === 'warning') return { background: '#fef3c7', color: '#92400e', border: '1px solid #fcd34d' }
  return                             { background: '#e0f2fe', color: '#075985', border: '1px solid #7dd3fc' }
}
</script>

<template>
  <div style="margin-top: 2rem; border-top: 2px solid #eee; padding-top: 1.5rem">

    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem">
      <div>
        <h2 style="margin: 0; font-size: 1.1rem">AI Inventory Auditor</h2>
        <p style="margin: 2px 0 0; font-size: 0.85rem; color: #666">
          Gemini analyses the full inventory and flags potential issues.
        </p>
      </div>
      <button
        @click="handleAudit"
        :disabled="loading"
        style="padding: 6px 18px; background: #4f46e5; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9rem; white-space: nowrap"
      >
        {{ loading ? 'Analysing…' : 'Run audit' }}
      </button>
    </div>

    <p v-if="error" style="color: red; font-size: 0.9rem">{{ error }}</p>

    <div v-if="ran && !loading">

      <!-- Summary -->
      <div style="background: #f9f9f9; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; font-size: 0.9rem; color: #333">
        {{ summary }}
      </div>

      <!-- No findings -->
      <p v-if="findings.length === 0" style="color: #16a34a; font-size: 0.9rem">
        ✓ No issues found — inventory looks clean.
      </p>

      <!-- Findings list -->
      <div
        v-for="(finding, i) in findings"
        :key="i"
        :style="{
          ...severityStyle(finding.severity),
          borderRadius: '8px',
          padding: '10px 14px',
          marginBottom: '8px',
          fontSize: '0.875rem',
        }"
      >
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 3px">
          <span style="font-weight: 600">{{ finding.item }}</span>
          <span :style="{
            fontSize: '0.75rem',
            fontWeight: '600',
            padding: '1px 7px',
            borderRadius: '8px',
            textTransform: 'uppercase',
            background: finding.severity === 'error' ? '#fca5a5' : finding.severity === 'warning' ? '#fcd34d' : '#7dd3fc',
            color: finding.severity === 'error' ? '#7f1d1d' : finding.severity === 'warning' ? '#78350f' : '#0c4a6e',
          }">{{ finding.severity }}</span>
        </div>
        <div>{{ finding.issue }}</div>
      </div>

    </div>

  </div>
</template>
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

function severityClass(severity) {
  if (severity === 'error') return 'error'
  if (severity === 'warning') return 'warning'
  return 'info'
}

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
</script>

<template>
  <div class="audit-panel">
    <div class="page-header tight-header">
      <div class="header-title">
        <h2>AI Inventory Auditor</h2>
        <p>Gemini reviews inventory quality and operational risks.</p>
      </div>
      <button class="btn btn-primary" :disabled="loading" @click="handleAudit">
        {{ loading ? 'Analysing...' : 'Run audit' }}
      </button>
    </div>

    <p v-if="error" class="alert-error">{{ error }}</p>

    <div v-if="ran && !loading">
      <div class="hint-card">
        <p>Audit summary</p>
        <p>{{ summary }}</p>
      </div>

      <p v-if="findings.length === 0" class="empty-state">No issues found. Inventory looks clean.</p>

      <div v-else class="audit-findings">
        <div
          v-for="(finding, i) in findings"
          :key="i"
          class="audit-item"
          :class="severityClass(finding.severity)"
        >
          <strong>{{ finding.item }}</strong>
          <span class="audit-tag">{{ finding.severity }}</span>
          <p class="issue-text">{{ finding.issue }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

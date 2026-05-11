<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">FC</span>
        <div>
          <strong>FastCharge Leads</strong>
          <small>外贸获客工作台</small>
        </div>
      </div>
      <button :class="{ active: activeTab === 'dashboard' }" @click="switchTab('dashboard')">Dashboard</button>
      <button :class="{ active: activeTab === 'leads' }" @click="switchTab('leads')">客户线索</button>
      <button :class="{ active: activeTab === 'emails' }" @click="switchTab('emails')">开发信审核</button>
    </aside>

    <main class="content">
      <header class="topbar">
        <div>
          <h1>{{ pageTitle }}</h1>
          <p>Vue3 前端通过 JSON API 调用 Python 后端，开发信发送前必须人工审核。</p>
        </div>
        <button class="ghost" @click="refreshCurrent">刷新</button>
      </header>

      <div v-if="message" class="toast">{{ message }}</div>
      <div v-if="error" class="toast error">{{ error }}</div>

      <section v-if="activeTab === 'dashboard'" class="stack">
        <div class="cards">
          <article class="card">
            <span>高分线索</span>
            <strong>{{ dashboard.top_leads?.length || 0 }}</strong>
          </article>
          <article v-for="status in statuses" :key="status" class="card">
            <span>{{ status }}</span>
            <strong>{{ dashboard.draft_counts?.[status] || 0 }}</strong>
          </article>
        </div>
        <DataTable title="Top leads" :columns="leadColumns" :rows="dashboard.top_leads || []" />
      </section>

      <section v-if="activeTab === 'leads'" class="stack">
        <div class="panel toolbar">
          <label>显示数量 <input v-model.number="leadLimit" type="number" min="1" max="1000" /></label>
          <button @click="loadLeads">加载线索</button>
        </div>
        <DataTable title="客户线索" :columns="leadColumns" :rows="leads" />
      </section>

      <section v-if="activeTab === 'emails'" class="stack">
        <div class="panel">
          <h2>生成开发信草稿</h2>
          <div class="form-grid">
            <label>数量 <input v-model.number="generateForm.limit" type="number" min="1" max="200" /></label>
            <label>最低评分 <input v-model.number="generateForm.min_score" type="number" min="0" max="100" /></label>
            <label>语言 <input v-model="generateForm.language" /></label>
            <button @click="generateDrafts">生成草稿</button>
          </div>
        </div>

        <div class="panel">
          <div class="section-heading">
            <h2>开发信草稿</h2>
            <div class="filters">
              <button :class="{ active: draftStatus === '' }" @click="setDraftStatus('')">all</button>
              <button v-for="status in statuses" :key="status" :class="{ active: draftStatus === status }" @click="setDraftStatus(status)">
                {{ status }} ({{ draftCounts[status] || 0 }})
              </button>
            </div>
          </div>
          <div class="sendbar">
            <label>发送数量 <input v-model.number="sendLimit" type="number" min="1" max="200" /></label>
            <button @click="sendApproved(true)">Dry-run 已审核</button>
            <button class="danger" @click="sendApproved(false)">发送已审核</button>
          </div>
          <div class="draft-layout">
            <div class="draft-list">
              <button
                v-for="draft in drafts"
                :key="draft.id"
                :class="{ selected: selectedDraft?.id === draft.id }"
                @click="loadDraft(draft.id)"
              >
                <strong>#{{ draft.id }} {{ draft.company_name }}</strong>
                <span>{{ draft.subject }}</span>
                <small>{{ draft.status }} · {{ draft.recipient_email }}</small>
              </button>
              <p v-if="!drafts.length" class="empty">暂无草稿。</p>
            </div>

            <div class="draft-detail panel">
              <template v-if="selectedDraft">
                <div class="section-heading">
                  <h2>草稿 #{{ selectedDraft.id }}</h2>
                  <span class="status">{{ selectedDraft.status }}</span>
                </div>
                <p class="muted">{{ selectedDraft.company_name }} · {{ selectedDraft.recipient_name || '联系人' }} &lt;{{ selectedDraft.recipient_email }}&gt;</p>
                <label>标题 <input v-model="selectedDraft.subject" /></label>
                <label>正文 <textarea v-model="selectedDraft.body" rows="16" /></label>
                <div class="actions">
                  <button @click="saveDraft">保存编辑</button>
                  <input v-model="reviewer" placeholder="审核人" />
                  <button @click="approveDraft">审核通过</button>
                  <button class="danger" @click="rejectDraft">拒绝</button>
                </div>
              </template>
              <p v-else class="empty">请选择一封开发信草稿。</p>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import {
  approveEmailDraft,
  generateEmailDrafts,
  getDashboard,
  getEmailDraft,
  getEmailDrafts,
  getLeads,
  rejectEmailDraft,
  sendApprovedDrafts,
  updateEmailDraft,
} from './api'

const DataTable = {
  props: {
    title: String,
    columns: Array,
    rows: Array,
  },
  template: `
    <div class="panel">
      <h2>{{ title }}</h2>
      <table>
        <thead>
          <tr><th v-for="column in columns" :key="column.key">{{ column.label }}</th></tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.id">
            <td v-for="column in columns" :key="column.key">{{ row[column.key] ?? '' }}</td>
          </tr>
          <tr v-if="!rows.length"><td :colspan="columns.length" class="empty">暂无数据。</td></tr>
        </tbody>
      </table>
    </div>
  `,
}

const statuses = ['draft', 'approved', 'rejected', 'sent', 'failed']
const activeTab = ref('dashboard')
const message = ref('')
const error = ref('')
const dashboard = ref({})
const leads = ref([])
const drafts = ref([])
const draftCounts = ref({})
const selectedDraft = ref(null)
const draftStatus = ref('')
const leadLimit = ref(100)
const sendLimit = ref(20)
const reviewer = ref('sales-manager')
const generateForm = reactive({ limit: 20, min_score: 70, language: 'English' })

const pageTitle = computed(() => {
  if (activeTab.value === 'leads') return '客户线索'
  if (activeTab.value === 'emails') return '开发信审核'
  return 'Dashboard'
})

const leadColumns = [
  { key: 'company_name', label: '公司' },
  { key: 'country', label: '国家' },
  { key: 'product_interest', label: '产品兴趣' },
  { key: 'domain', label: '域名' },
  { key: 'customs_matches', label: '海关匹配' },
  { key: 'contact_count', label: '联系人' },
  { key: 'score', label: '评分' },
]

function notify(text) {
  message.value = text
  error.value = ''
}

function fail(exc) {
  error.value = exc.message || String(exc)
  message.value = ''
}

async function run(action) {
  try {
    await action()
  } catch (exc) {
    fail(exc)
  }
}

function switchTab(tab) {
  activeTab.value = tab
  refreshCurrent()
}

function refreshCurrent() {
  if (activeTab.value === 'dashboard') return loadDashboard()
  if (activeTab.value === 'leads') return loadLeads()
  return loadDrafts()
}

async function loadDashboard() {
  await run(async () => {
    dashboard.value = await getDashboard()
  })
}

async function loadLeads() {
  await run(async () => {
    const data = await getLeads(leadLimit.value)
    leads.value = data.items
  })
}

async function loadDrafts() {
  await run(async () => {
    const data = await getEmailDrafts({ status: draftStatus.value, limit: 100 })
    drafts.value = data.items
    draftCounts.value = data.draft_counts
    if (selectedDraft.value && !drafts.value.some((draft) => draft.id === selectedDraft.value.id)) {
      selectedDraft.value = null
    }
  })
}

function setDraftStatus(status) {
  draftStatus.value = status
  loadDrafts()
}

async function loadDraft(id) {
  await run(async () => {
    selectedDraft.value = await getEmailDraft(id)
  })
}

async function generateDrafts() {
  await run(async () => {
    const result = await generateEmailDrafts(generateForm)
    notify(`已生成 ${result.created} 封开发信草稿`)
    await loadDrafts()
  })
}

async function saveDraft() {
  if (!selectedDraft.value) return
  await run(async () => {
    selectedDraft.value = await updateEmailDraft(selectedDraft.value.id, {
      subject: selectedDraft.value.subject,
      body: selectedDraft.value.body,
    })
    notify('草稿已保存，状态已重置为 draft')
    await loadDrafts()
  })
}

async function approveDraft() {
  if (!selectedDraft.value) return
  await run(async () => {
    selectedDraft.value = await approveEmailDraft(selectedDraft.value.id, reviewer.value)
    notify('草稿已审核通过')
    await loadDrafts()
  })
}

async function rejectDraft() {
  if (!selectedDraft.value) return
  await run(async () => {
    selectedDraft.value = await rejectEmailDraft(selectedDraft.value.id, reviewer.value)
    notify('草稿已拒绝')
    await loadDrafts()
  })
}

async function sendApproved(dryRun) {
  await run(async () => {
    const result = await sendApprovedDrafts({ limit: sendLimit.value, dry_run: dryRun })
    notify(`${dryRun ? 'Dry-run 匹配' : '已发送'} ${result.sent} 封，失败 ${result.failed} 封`)
    await loadDrafts()
  })
}

onMounted(() => {
  loadDashboard()
})
</script>

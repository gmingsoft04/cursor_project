<template>
  <div v-if="!user" class="login-screen">
    <form class="login-card" @submit.prevent="submitLogin">
      <span class="brand-mark">FC</span>
      <h1>FastCharge Leads</h1>
      <p>请登录后使用客户线索、开发信审核和发送功能。</p>
      <label>用户名 <input v-model="loginForm.username" autocomplete="username" /></label>
      <label>密码 <input v-model="loginForm.password" type="password" autocomplete="current-password" /></label>
      <button type="submit">登录</button>
      <div v-if="error" class="toast error">{{ error }}</div>
    </form>
  </div>

  <div v-else class="app-shell">
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
      <button :class="{ active: activeTab === 'audit' }" @click="switchTab('audit')">操作日志</button>
    </aside>

    <main class="content">
      <header class="topbar">
        <div>
          <h1>{{ pageTitle }}</h1>
          <p>Vue3 前端通过 JSON API 调用 Python 后端，开发信发送前必须人工审核。</p>
        </div>
        <div class="userbar">
          <span>{{ user.username }}</span>
          <button class="ghost" @click="refreshCurrent">刷新</button>
          <button class="ghost" @click="submitLogout">退出</button>
        </div>
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
        <div class="panel">
          <h2>客户线索与 CRM 跟进</h2>
          <table>
            <thead>
              <tr>
                <th>公司</th><th>国家</th><th>产品</th><th>评分</th><th>CRM 状态</th><th>负责人</th><th>下次跟进</th><th>备注</th><th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="lead in leads" :key="lead.id">
                <td>{{ lead.company_name }}</td>
                <td>{{ lead.country }}</td>
                <td>{{ lead.product_interest }}</td>
                <td>{{ lead.score }}</td>
                <td>
                  <select v-model="lead.crm_status">
                    <option v-for="status in crmStatuses" :key="status" :value="status">{{ status }}</option>
                  </select>
                </td>
                <td><input v-model="lead.owner" placeholder="负责人" /></td>
                <td><input v-model="lead.next_follow_up_at" placeholder="YYYY-MM-DD" /></td>
                <td><input v-model="lead.crm_notes" placeholder="跟进备注" /></td>
                <td><button @click="saveLeadCrm(lead)">保存</button></td>
              </tr>
              <tr v-if="!leads.length"><td colspan="9" class="empty">暂无线索。</td></tr>
            </tbody>
          </table>
        </div>
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

      <section v-if="activeTab === 'audit'" class="stack">
        <div class="panel toolbar">
          <label>显示数量 <input v-model.number="auditLimit" type="number" min="1" max="500" /></label>
          <button @click="loadAuditLogs">加载日志</button>
        </div>
        <div class="panel">
          <h2>操作日志</h2>
          <table>
            <thead>
              <tr><th>时间</th><th>用户</th><th>动作</th><th>对象</th><th>详情</th></tr>
            </thead>
            <tbody>
              <tr v-for="log in auditLogs" :key="log.id">
                <td>{{ log.created_at }}</td>
                <td>{{ log.actor }}</td>
                <td>{{ log.action }}</td>
                <td>{{ log.entity_type || '' }} {{ log.entity_id || '' }}</td>
                <td><code>{{ JSON.stringify(log.metadata) }}</code></td>
              </tr>
              <tr v-if="!auditLogs.length"><td colspan="5" class="empty">暂无操作日志。</td></tr>
            </tbody>
          </table>
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
  getAuditLogs,
  getCurrentUser,
  getDashboard,
  getEmailDraft,
  getEmailDrafts,
  getLeads,
  getStoredToken,
  login,
  logout,
  rejectEmailDraft,
  sendApprovedDrafts,
  updateLeadCrm,
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
const crmStatuses = ['new', 'contacted', 'replied', 'quoted', 'sample', 'negotiating', 'won', 'lost', 'invalid']
const activeTab = ref('dashboard')
const message = ref('')
const error = ref('')
const user = ref(null)
const dashboard = ref({})
const leads = ref([])
const auditLogs = ref([])
const drafts = ref([])
const draftCounts = ref({})
const selectedDraft = ref(null)
const draftStatus = ref('')
const leadLimit = ref(100)
const auditLimit = ref(100)
const sendLimit = ref(20)
const reviewer = ref('sales-manager')
const generateForm = reactive({ limit: 20, min_score: 70, language: 'English' })
const loginForm = reactive({ username: 'admin', password: '' })

const pageTitle = computed(() => {
  if (activeTab.value === 'leads') return '客户线索'
  if (activeTab.value === 'emails') return '开发信审核'
  if (activeTab.value === 'audit') return '操作日志'
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
  if (activeTab.value === 'audit') return loadAuditLogs()
  return loadDrafts()
}

async function submitLogin() {
  await run(async () => {
    const data = await login(loginForm.username, loginForm.password)
    user.value = data.user
    notify('登录成功')
    await loadDashboard()
  })
}

async function submitLogout() {
  await run(async () => {
    await logout()
    user.value = null
    dashboard.value = {}
    leads.value = []
    drafts.value = []
    selectedDraft.value = null
    notify('已退出')
  })
}

async function restoreSession() {
  if (!getStoredToken()) return
  await run(async () => {
    user.value = await getCurrentUser()
    await loadDashboard()
  })
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

async function loadAuditLogs() {
  await run(async () => {
    const data = await getAuditLogs(auditLimit.value)
    auditLogs.value = data.items
  })
}

async function saveLeadCrm(lead) {
  await run(async () => {
    const updated = await updateLeadCrm(lead.id, {
      crm_status: lead.crm_status,
      owner: lead.owner,
      next_follow_up_at: lead.next_follow_up_at,
      crm_notes: lead.crm_notes,
    })
    Object.assign(lead, updated)
    notify('CRM 跟进状态已保存')
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
  restoreSession()
})
</script>

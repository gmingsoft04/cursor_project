<template>
  <div>
    <div class="page-card">
      <h3 class="section-title">第 1 步：选择模板</h3>
      <el-select v-model="form.template_id" placeholder="选择模板" style="width:360px" @change="onTplChange">
        <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id" />
      </el-select>
      <span class="muted" style="margin-left:12px">或在下方手动输入主题/正文</span>
      <el-form :model="form" label-width="60px" style="margin-top:14px">
        <el-form-item label="主题"><el-input v-model="form.subject" /></el-form-item>
        <el-form-item label="正文">
          <el-input v-model="form.body" type="textarea" :rows="10" />
        </el-form-item>
        <el-form-item label="格式">
          <el-radio-group v-model="form.is_html">
            <el-radio :value="true">HTML</el-radio>
            <el-radio :value="false">纯文本</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
    </div>

    <div class="page-card">
      <h3 class="section-title">第 2 步：选择收件人</h3>
      <div class="toolbar">
        <el-radio-group v-model="recipientMode">
          <el-radio-button value="all">全部可发送客户</el-radio-button>
          <el-radio-button value="pick">从列表勾选</el-radio-button>
        </el-radio-group>
        <el-input
          v-if="recipientMode === 'pick'"
          v-model="q"
          placeholder="搜索"
          clearable
          style="width:240px"
          @keyup.enter="loadCustomers"
        />
        <el-button v-if="recipientMode === 'pick'" @click="loadCustomers">筛选</el-button>
        <span class="grow" />
        <el-tag type="success">已退订客户会自动跳过</el-tag>
      </div>
      <el-table
        v-if="recipientMode === 'pick'"
        :data="customers"
        stripe
        max-height="380"
        @selection-change="(rows) => (selected = rows)"
      >
        <el-table-column type="selection" width="44" :selectable="(row) => !row.unsubscribed" />
        <el-table-column prop="email" label="邮箱" min-width="220">
          <template #default="{ row }">
            {{ row.email }}
            <el-tag v-if="row.unsubscribed" size="small" type="danger" style="margin-left:6px">退订</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="姓名" min-width="120" />
        <el-table-column prop="company" label="公司" min-width="160" show-overflow-tooltip />
        <el-table-column prop="country" label="国家" width="90" />
      </el-table>
      <div v-if="recipientMode === 'pick'" style="margin-top:8px" class="muted">
        已勾选 {{ selected.length }} 位
      </div>
    </div>

    <div class="page-card">
      <h3 class="section-title">第 3 步：预览并发送</h3>
      <div class="toolbar">
        <el-button @click="doPreview" :loading="previewing">
          <el-icon><View /></el-icon>预览渲染
        </el-button>
        <el-button type="primary" :loading="sending" @click="doSend">
          <el-icon><Promotion /></el-icon>开始群发
        </el-button>
      </div>
      <div v-if="preview.subject">
        <div class="muted" style="margin-bottom:6px">
          示例收件人：<b>{{ preview.sample_to }}</b> · 待发送 {{ preview.will_send }} / 跳过退订 {{ preview.will_skip_unsubscribed }} · 共 {{ preview.total }}
        </div>
        <div class="muted" style="margin-bottom:6px">主题：<b>{{ preview.subject }}</b></div>
        <iframe
          v-if="preview.is_html"
          class="email-preview-frame"
          :srcdoc="preview.body"
        ></iframe>
        <pre v-else style="white-space:pre-wrap;background:#f9fafb;padding:14px;border-radius:6px">{{ preview.body }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const templates = ref([])
const customers = ref([])
const selected = ref([])
const recipientMode = ref('all')
const q = ref('')
const previewing = ref(false)
const sending = ref(false)
const preview = ref({})

const form = reactive({
  template_id: null,
  subject: '',
  body: '',
  is_html: true,
  name: ''
})

onMounted(async () => {
  templates.value = (await api.get('/api/templates')).data
  if (templates.value.length) {
    form.template_id = templates.value[0].id
    onTplChange(form.template_id)
  }
  loadCustomers()
})

function onTplChange(id) {
  const t = templates.value.find((x) => x.id === id)
  if (!t) return
  form.subject = t.subject
  form.body = t.body
  form.is_html = t.is_html
}

async function loadCustomers() {
  const params = { page: 1, page_size: 200 }
  if (q.value) params.q = q.value
  const r = await api.get('/api/customers', { params })
  customers.value = r.data.items
}

function payloadFromForm() {
  const payload = {
    template_id: form.template_id || null,
    subject: form.subject,
    body: form.body,
    is_html: form.is_html
  }
  if (recipientMode.value === 'all') {
    payload.send_all_active = true
  } else {
    payload.customer_ids = selected.value.map((x) => x.id)
    if (!payload.customer_ids.length) throw new Error('请至少勾选一位收件人')
  }
  return payload
}

async function doPreview() {
  try {
    previewing.value = true
    const r = await api.post('/api/campaigns/preview', payloadFromForm())
    preview.value = r.data
  } catch (e) {
    if (e.message && !e.response) ElMessage.warning(e.message)
  } finally {
    previewing.value = false
  }
}

async function doSend() {
  try {
    const payload = payloadFromForm()
    payload.name = form.name || `Campaign ${new Date().toLocaleString()}`
    await ElMessageBox.confirm(
      recipientMode.value === 'all'
        ? '将向所有「未退订」的客户发送，是否继续？'
        : `将向勾选的 ${payload.customer_ids.length} 位客户发送（其中已退订者将自动跳过），是否继续？`,
      '确认群发',
      { type: 'warning' }
    )
    sending.value = true
    const r = await api.post('/api/campaigns/send', payload)
    ElMessage.success(`完成：成功 ${r.data.succeeded} / 失败 ${r.data.failed} / 跳过 ${r.data.skipped}`)
  } catch (e) {
    if (e.message && !e.response && e !== 'cancel') ElMessage.warning(e.message)
  } finally {
    sending.value = false
  }
}
</script>

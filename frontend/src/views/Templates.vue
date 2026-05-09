<template>
  <div>
    <div class="page-card">
      <h3 class="section-title">开发信模板</h3>
      <p class="muted" style="margin-top:-6px" v-pre>
        模板支持 Jinja 变量：<code>{{first_name}}</code>、<code>{{name}}</code>、<code>{{company}}</code>、
        <code>{{country}}</code>、<code>{{position}}</code>、<code>{{sender_name}}</code>、
        <code>{{unsubscribe_url}}</code>。系统会自动在邮件末尾插入退订链接（如未引用）。
      </p>
      <div class="toolbar">
        <el-button type="primary" @click="newTpl"><el-icon><Plus /></el-icon>新建模板</el-button>
      </div>
      <el-row :gutter="16">
        <el-col :span="9">
          <el-table :data="list" highlight-current-row @current-change="select" max-height="540">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="name" label="名称" min-width="180" show-overflow-tooltip />
            <el-table-column label="类型" width="80">
              <template #default="{ row }">
                <el-tag size="small" :type="row.is_html ? 'success' : 'info'">{{ row.is_html ? 'HTML' : 'Plain' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-col>
        <el-col :span="15">
          <div v-if="!current.id && !creating" class="muted" style="padding:24px;text-align:center">
            选择左侧模板进行编辑，或点击「新建模板」。
          </div>
          <div v-else>
            <el-form :model="current" label-width="76px">
              <el-form-item label="名称">
                <el-input v-model="current.name" />
              </el-form-item>
              <el-form-item label="主题">
                <el-input v-model="current.subject" placeholder="支持 {{company}} 等变量" />
              </el-form-item>
              <el-form-item label="格式">
                <el-radio-group v-model="current.is_html">
                  <el-radio :value="true">HTML</el-radio>
                  <el-radio :value="false">纯文本</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="正文">
                <el-input v-model="current.body" type="textarea" :rows="14" />
              </el-form-item>
              <el-form-item label="说明">
                <el-input v-model="current.description" />
              </el-form-item>
            </el-form>
            <div style="text-align:right">
              <el-button v-if="current.id" type="danger" plain @click="del">删除</el-button>
              <el-button type="primary" @click="save">保存</el-button>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const list = ref([])
const current = ref({})
const creating = ref(false)

async function load(idToSelect) {
  const r = await api.get('/api/templates')
  list.value = r.data
  if (idToSelect) {
    const t = list.value.find((x) => x.id === idToSelect)
    if (t) current.value = { ...t }
  }
}
onMounted(load)

function select(row) {
  if (!row) return
  creating.value = false
  current.value = { ...row }
}

function newTpl() {
  creating.value = true
  current.value = {
    name: '新模板',
    subject: 'Charging products quotation for {{ company }}',
    is_html: true,
    body: '<p>Hi {{ first_name }},</p>\n<p>...</p>\n<p>Best,<br>{{ sender_name }}</p>',
    description: ''
  }
}

async function save() {
  if (!current.value.name || !current.value.subject || !current.value.body) {
    return ElMessage.warning('名称 / 主题 / 正文 不能为空')
  }
  if (current.value.id) {
    const id = current.value.id
    const payload = { ...current.value }
    delete payload.id
    delete payload.created_at
    delete payload.updated_at
    await api.patch(`/api/templates/${id}`, payload)
    ElMessage.success('已保存')
    await load(id)
  } else {
    const r = await api.post('/api/templates', current.value)
    ElMessage.success('已创建')
    creating.value = false
    await load(r.data.id)
  }
}

async function del() {
  await ElMessageBox.confirm(`删除模板 ${current.value.name}？`, '提示', { type: 'warning' })
  await api.delete(`/api/templates/${current.value.id}`)
  ElMessage.success('已删除')
  current.value = {}
  load()
}
</script>

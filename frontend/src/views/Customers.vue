<template>
  <div>
    <div class="page-card">
      <h3 class="section-title">客户管理</h3>
      <div class="toolbar">
        <el-input
          v-model="q"
          placeholder="搜索邮箱 / 姓名 / 公司 / 国家"
          clearable
          style="width:280px"
          @keyup.enter="load"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="unsubscribed" placeholder="状态" clearable style="width:140px">
          <el-option label="可发送" :value="false" />
          <el-option label="已退订" :value="true" />
        </el-select>
        <el-button type="primary" @click="load">查询</el-button>
        <span class="grow" />
        <el-button @click="dialogAdd = true"><el-icon><Plus /></el-icon>手动添加</el-button>
        <el-button :disabled="!selected.length" type="danger" @click="batchUnsubscribe">
          标记退订 ({{ selected.length }})
        </el-button>
        <el-button :disabled="!selected.length" type="warning" @click="batchDelete">
          删除 ({{ selected.length }})
        </el-button>
      </div>

      <el-table
        :data="items"
        stripe
        @selection-change="(rows) => (selected = rows)"
        max-height="600"
        empty-text="暂无客户"
      >
        <el-table-column type="selection" width="44" />
        <el-table-column prop="email" label="邮箱" min-width="220" sortable>
          <template #default="{ row }">
            {{ row.email }}
            <el-tag v-if="row.unsubscribed" size="small" type="danger" style="margin-left:6px">退订</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="姓名" min-width="120" />
        <el-table-column prop="company" label="公司" min-width="160" show-overflow-tooltip />
        <el-table-column prop="position" label="职位" min-width="140" show-overflow-tooltip />
        <el-table-column prop="country" label="国家" width="90" />
        <el-table-column prop="keyword" label="关键字" min-width="140" show-overflow-tooltip />
        <el-table-column prop="source" label="来源" width="90" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="edit(row)">编辑</el-button>
            <el-button
              size="small"
              :type="row.unsubscribed ? 'success' : 'warning'"
              @click="toggleUnsub(row)"
            >
              {{ row.unsubscribed ? '取消退订' : '标记退订' }}
            </el-button>
            <el-button size="small" type="danger" @click="del(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        background
        layout="total, prev, pager, next, sizes"
        :total="total"
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        @current-change="load"
        @size-change="load"
        style="margin-top:12px;justify-content:flex-end"
      />
    </div>

    <el-dialog v-model="dialogAdd" title="添加客户" width="520px" @close="resetForm">
      <el-form :model="form" label-width="80px">
        <el-form-item label="邮箱" required>
          <el-input v-model="form.email" placeholder="user@example.com" />
        </el-form-item>
        <el-form-item label="姓名"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="公司"><el-input v-model="form.company" /></el-form-item>
        <el-form-item label="职位"><el-input v-model="form.position" /></el-form-item>
        <el-form-item label="国家"><el-input v-model="form.country" /></el-form-item>
        <el-form-item label="网站"><el-input v-model="form.website" /></el-form-item>
        <el-form-item label="关键字"><el-input v-model="form.keyword" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogAdd = false">取消</el-button>
        <el-button type="primary" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="dialogEdit" title="编辑客户" width="520px">
      <el-form :model="editing" label-width="80px">
        <el-form-item label="邮箱"><el-input :model-value="editing.email" disabled /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="editing.name" /></el-form-item>
        <el-form-item label="公司"><el-input v-model="editing.company" /></el-form-item>
        <el-form-item label="职位"><el-input v-model="editing.position" /></el-form-item>
        <el-form-item label="国家"><el-input v-model="editing.country" /></el-form-item>
        <el-form-item label="网站"><el-input v-model="editing.website" /></el-form-item>
        <el-form-item label="关键字"><el-input v-model="editing.keyword" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="editing.notes" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="退订">
          <el-switch v-model="editing.unsubscribed" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogEdit = false">取消</el-button>
        <el-button type="primary" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const q = ref('')
const unsubscribed = ref(null)
const selected = ref([])

const dialogAdd = ref(false)
const dialogEdit = ref(false)
const form = ref({})
const editing = ref({})

async function load() {
  const params = { page: page.value, page_size: pageSize.value }
  if (q.value) params.q = q.value
  if (unsubscribed.value !== null && unsubscribed.value !== '') params.unsubscribed = unsubscribed.value
  const r = await api.get('/api/customers', { params })
  items.value = r.data.items
  total.value = r.data.total
}
onMounted(load)

function resetForm() {
  form.value = {}
}

async function submitForm() {
  if (!form.value.email) return ElMessage.warning('请输入邮箱')
  await api.post('/api/customers', form.value)
  ElMessage.success('已添加')
  dialogAdd.value = false
  resetForm()
  load()
}

function edit(row) {
  editing.value = { ...row }
  dialogEdit.value = true
}

async function submitEdit() {
  const id = editing.value.id
  const payload = { ...editing.value }
  delete payload.id
  delete payload.email
  delete payload.created_at
  delete payload.updated_at
  delete payload.unsubscribed_at
  await api.patch(`/api/customers/${id}`, payload)
  ElMessage.success('已保存')
  dialogEdit.value = false
  load()
}

async function toggleUnsub(row) {
  await api.patch(`/api/customers/${row.id}`, { unsubscribed: !row.unsubscribed })
  load()
}

async function del(row) {
  await ElMessageBox.confirm(`确定删除 ${row.email}?`, '提示', { type: 'warning' })
  await api.delete(`/api/customers/${row.id}`)
  ElMessage.success('已删除')
  load()
}

async function batchUnsubscribe() {
  await ElMessageBox.confirm(`将 ${selected.value.length} 位客户标记为退订？`, '提示', { type: 'warning' })
  for (const row of selected.value) {
    await api.patch(`/api/customers/${row.id}`, { unsubscribed: true })
  }
  ElMessage.success('已更新')
  load()
}

async function batchDelete() {
  await ElMessageBox.confirm(`确定删除 ${selected.value.length} 位客户？`, '危险操作', { type: 'warning' })
  for (const row of selected.value) {
    await api.delete(`/api/customers/${row.id}`)
  }
  ElMessage.success('已删除')
  load()
}
</script>

<template>
  <div>
    <div class="page-card">
      <h3 class="section-title">客户搜索</h3>
      <p class="muted" style="margin-top:-6px">
        通过关键字（如 <code>phone charger importer USA</code>）或域名（如 <code>example.com</code>）寻找潜在客户邮箱。
        勾选后保存到本地，可在「客户管理」中进一步整理。
      </p>
      <div class="toolbar">
        <el-input
          v-model="keyword"
          placeholder="输入关键字或域名 / Keyword or domain"
          class="grow"
          clearable
          @keyup.enter="doSearch"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="provider" placeholder="提供方" style="width:140px" clearable>
          <el-option
            v-for="p in providers"
            :key="p"
            :label="p"
            :value="p"
          />
        </el-select>
        <el-input-number v-model="limit" :min="1" :max="50" :step="5" />
        <el-button type="primary" :loading="loading" @click="doSearch">
          <el-icon><Search /></el-icon>搜索
        </el-button>
        <el-button :disabled="!selected.length" @click="saveSelected" type="success">
          <el-icon><Plus /></el-icon>保存所选 ({{ selected.length }})
        </el-button>
      </div>
      <el-alert v-if="notice" :title="notice" type="info" show-icon :closable="false" style="margin-bottom:12px" />
      <el-table
        :data="items"
        stripe
        @selection-change="(rows) => (selected = rows)"
        empty-text="尚未搜索"
        max-height="540"
      >
        <el-table-column type="selection" width="44" :selectable="(row) => !row.already_exists" />
        <el-table-column prop="email" label="邮箱" min-width="220">
          <template #default="{ row }">
            {{ row.email }}
            <el-tag v-if="row.already_exists" size="small" type="info" style="margin-left:6px">已存在</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="姓名" min-width="120" />
        <el-table-column prop="company" label="公司" min-width="160" show-overflow-tooltip />
        <el-table-column prop="position" label="职位" min-width="140" show-overflow-tooltip />
        <el-table-column prop="country" label="国家" width="100" />
        <el-table-column prop="confidence" label="置信度" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.confidence != null" :type="row.confidence >= 80 ? 'success' : row.confidence >= 50 ? 'warning' : 'info'">
              {{ row.confidence }}
            </el-tag>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="90" />
        <el-table-column prop="website" label="网站" min-width="180">
          <template #default="{ row }">
            <a v-if="row.website" :href="row.website" target="_blank">{{ row.website }}</a>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const keyword = ref('phone charger importer')
const provider = ref('')
const limit = ref(15)
const items = ref([])
const selected = ref([])
const loading = ref(false)
const notice = ref('')
const providers = ref([])

onMounted(async () => {
  const r = await api.get('/api/search/providers')
  providers.value = r.data.providers
})

async function doSearch() {
  if (!keyword.value.trim()) {
    ElMessage.warning('请输入关键字或域名')
    return
  }
  loading.value = true
  try {
    const r = await api.post('/api/search', {
      keyword: keyword.value,
      provider: provider.value || null,
      limit: limit.value
    })
    items.value = r.data.items || []
    notice.value = r.data.notice || ''
    if (!items.value.length) ElMessage.info('未找到结果')
  } finally {
    loading.value = false
  }
}

async function saveSelected() {
  if (!selected.value.length) return
  const r = await api.post('/api/search/save', { items: selected.value })
  ElMessage.success(`新增 ${r.data.inserted} 位，跳过 ${r.data.skipped} 位（已存在）`)
  // 标记本批次为已存在，避免重复保存
  for (const row of selected.value) row.already_exists = true
}
</script>

<template>
  <div>
    <div class="stat-grid">
      <div class="stat-card">
        <div class="label">客户总数</div>
        <div class="value">{{ stats.total ?? '-' }}</div>
      </div>
      <div class="stat-card green">
        <div class="label">可发送 (未退订)</div>
        <div class="value">{{ stats.active ?? '-' }}</div>
      </div>
      <div class="stat-card red">
        <div class="label">已退订</div>
        <div class="value">{{ stats.unsubscribed ?? '-' }}</div>
      </div>
      <div class="stat-card gray">
        <div class="label">开发信模板</div>
        <div class="value">{{ templateCount }}</div>
      </div>
    </div>

    <div class="page-card" style="margin-top:20px">
      <h3 class="section-title">快速开始</h3>
      <ol class="muted" style="line-height:1.9;font-size:14px">
        <li>在 <b>系统设置</b> 中确认 SMTP 与搜索 API key（也可直接在 .env 中配置）。</li>
        <li>到 <b>客户搜索</b> 输入关键词（例：<code>phone charger importer USA</code>）或域名（例：<code>example.com</code>），勾选感兴趣的邮箱保存到本地数据库。</li>
        <li>在 <b>开发信模板</b> 维护多套话术，支持 <code v-pre>{{first_name}}</code>、<code v-pre>{{company}}</code>、<code v-pre>{{unsubscribe_url}}</code> 等占位符。</li>
        <li>到 <b>群发开发信</b> 选择模板和收件人，先 <b>预览</b> 再 <b>发送</b>，已退订客户会被自动跳过。</li>
      </ol>
    </div>

    <div class="page-card">
      <h3 class="section-title">最近的群发任务</h3>
      <el-table :data="campaigns" stripe size="small" empty-text="暂无群发记录">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="任务名称" min-width="200" />
        <el-table-column prop="subject" label="主题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="total" label="总数" width="80" />
        <el-table-column prop="succeeded" label="成功" width="80" />
        <el-table-column prop="failed" label="失败" width="80" />
        <el-table-column prop="skipped" label="跳过" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'completed' ? 'success' : 'info'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="180" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import api from '../api'

const stats = ref({})
const templateCount = ref(0)
const campaigns = ref([])

async function load() {
  const [s, t, c] = await Promise.all([
    api.get('/api/customers/_/stats'),
    api.get('/api/templates'),
    api.get('/api/campaigns')
  ])
  stats.value = s.data
  templateCount.value = t.data.length
  campaigns.value = c.data.slice(0, 10)
}

onMounted(load)
</script>

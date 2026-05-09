<template>
  <div>
    <div class="page-card">
      <h3 class="section-title">系统状态</h3>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="应用名称">{{ s.app_name }}</el-descriptions-item>
        <el-descriptions-item label="对外基地址 (退订链接使用)">{{ s.app_base_url }}</el-descriptions-item>
        <el-descriptions-item label="SMTP">
          <el-tag v-if="s.smtp_configured" type="success">已配置</el-tag>
          <el-tag v-else type="warning">未配置</el-tag>
          <span v-if="s.smtp_from_email" style="margin-left:10px">{{ s.smtp_from_email }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="可用搜索源">
          <el-tag
            v-for="p in s.providers_available"
            :key="p"
            style="margin-right:6px"
          >{{ p }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <div class="page-card">
      <h3 class="section-title">如何配置</h3>
      <p class="muted">
        所有设置通过后端项目根目录下的 <code>.env</code> 文件管理（参考 <code>.env.example</code>）。
        修改后重启后端进程生效。
      </p>
      <pre style="background:#0f172a;color:#e2e8f0;padding:16px;border-radius:8px;overflow:auto">
APP_BASE_URL=https://your-domain.com   # 退订链接需公网可访问
SECRET_KEY=please-change-me
HUNTER_API_KEY=...                     # 可选：商业邮箱搜索 (https://hunter.io/api)
SERPAPI_KEY=...                        # 可选：关键字 -> 公司域名 (https://serpapi.com)

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@example.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_FROM_NAME=Your Name
SMTP_FROM_EMAIL=your@example.com
SEND_BATCH_INTERVAL=2                  # 单封邮件之间的间隔秒数
      </pre>
      <p class="muted">
        提示：若使用 Gmail 请使用应用专用密码；若使用 QQ/163 邮箱请使用授权码。建议在自己的域名下配置 SPF / DKIM 以提高送达率。
      </p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import api from '../api'

const s = ref({})

onMounted(async () => {
  s.value = (await api.get('/api/settings')).data
})
</script>

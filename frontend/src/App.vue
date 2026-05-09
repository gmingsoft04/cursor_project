<template>
  <el-container class="app-layout">
    <el-aside width="220px" class="app-aside">
      <div class="logo">
        <el-icon><Connection /></el-icon>
        <span>外贸客户开发系统</span>
      </div>
      <el-menu
        :default-active="route.path"
        router
        background-color="transparent"
        text-color="#d1d5db"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/">
          <el-icon><DataLine /></el-icon><span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/search">
          <el-icon><Search /></el-icon><span>客户搜索</span>
        </el-menu-item>
        <el-menu-item index="/customers">
          <el-icon><User /></el-icon><span>客户管理</span>
        </el-menu-item>
        <el-menu-item index="/templates">
          <el-icon><Document /></el-icon><span>开发信模板</span>
        </el-menu-item>
        <el-menu-item index="/campaigns">
          <el-icon><Promotion /></el-icon><span>群发开发信</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon><span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header" height="56px">
        <div style="font-weight:600;color:#111827">{{ pageTitle }}</div>
        <div class="muted">
          <el-tag v-if="settings.smtp_configured" type="success" size="small">SMTP 已配置</el-tag>
          <el-tag v-else type="warning" size="small">SMTP 未配置</el-tag>
          <span style="margin-left:12px">搜索源：{{ (settings.providers_available || []).join(', ') }}</span>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from './api'

const route = useRoute()
const settings = ref({})

const titleMap = {
  '/': '仪表盘',
  '/search': '客户搜索',
  '/customers': '客户管理',
  '/templates': '开发信模板',
  '/campaigns': '群发开发信',
  '/settings': '系统设置'
}

const pageTitle = computed(() => titleMap[route.path] || '')

onMounted(async () => {
  try {
    settings.value = (await api.get('/api/settings')).data
  } catch (e) {
    /* ignore */
  }
})
</script>

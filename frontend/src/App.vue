<template>
  <div class="app-container">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside width="240px" v-if="showLayout" class="aside-panel">
        <div class="logo-section">
          <div class="logo-icon">🛒</div>
          <div class="logo-text">
            <h2>Buyer Radar</h2>
            <p>AI海外采购商雷达</p>
          </div>
        </div>

        <el-menu
          :default-active="activeMenu"
          router
          class="sidebar-menu"
          :ellipsis="false"
        >
          <el-menu-item index="/">
            <el-icon><HomeFilled /></el-icon>
            <span>首页概览</span>
          </el-menu-item>
          <el-menu-item index="/buyers">
            <el-icon><User /></el-icon>
            <span>采购商列表</span>
          </el-menu-item>
          <el-menu-item index="/import">
            <el-icon><Upload /></el-icon>
            <span>数据导入</span>
          </el-menu-item>
          <el-menu-item index="/search">
            <el-icon><Search /></el-icon>
            <span>智能搜索</span>
          </el-menu-item>
          <el-menu-item index="/crm">
            <el-icon><ChatDotRound /></el-icon>
            <span>CRM跟进</span>
          </el-menu-item>
          <el-menu-item index="/outreach">
            <el-icon><Message /></el-icon>
            <span>AI联系</span>
          </el-menu-item>
          <el-menu-item index="/export">
            <el-icon><Download /></el-icon>
            <span>数据导出</span>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
        </el-menu>

        <div class="sidebar-footer">
          <div class="version-tag">v1.0.0</div>
        </div>
      </el-aside>

      <!-- 主内容 -->
      <el-main class="main-panel">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { HomeFilled, User, Upload, Search, ChatDotRound, Message, Download, Setting } from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
const showLayout = computed(() => route.path !== '/')
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --sidebar-bg: #0f1623;
  --sidebar-gradient-start: #0f1623;
  --sidebar-gradient-end: #1a2332;
  --sidebar-border: rgba(255,255,255,0.06);
  --sidebar-item-hover: rgba(255,255,255,0.06);
  --sidebar-item-active: rgba(99,102,241,0.2);
  --sidebar-item-active-border: #6366f1;
  --sidebar-text: rgba(255,255,255,0.7);
  --sidebar-text-active: #ffffff;
  --sidebar-icon: rgba(255,255,255,0.5);
  --sidebar-icon-active: #6366f1;
  --accent-primary: #6366f1;
  --accent-secondary: #8b5cf6;
  --accent-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  --bg-page: #f1f5f9;
  --bg-card: #ffffff;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
  --shadow-lg: 0 10px 40px rgba(0,0,0,0.12);
  --radius-lg: 16px;
  --radius-md: 12px;
  --radius-sm: 8px;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg-page);
  color: #1e293b;
  -webkit-font-smoothing: antialiased;
}

.app-container {
  height: 100vh;
  overflow: hidden;
}

/* ====== 侧边栏 ====== */
.aside-panel {
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--sidebar-border);
  overflow: hidden;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 24px 20px;
  border-bottom: 1px solid var(--sidebar-border);
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: var(--accent-gradient);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(99,102,241,0.3);
}

.logo-text h2 {
  font-size: 15px;
  font-weight: 700;
  color: white;
  letter-spacing: -0.02em;
}

.logo-text p {
  font-size: 11px;
  color: var(--sidebar-text);
  margin-top: 2px;
}

.sidebar-menu {
  border-right: none !important;
  background: transparent;
  flex: 1;
  padding: 12px 0;
}

.sidebar-menu .el-menu-item {
  margin: 4px 12px;
  border-radius: var(--radius-sm);
  padding-left: 16px !important;
  height: 42px;
  line-height: 42px;
  color: var(--sidebar-text);
  font-size: 13.5px;
  font-weight: 500;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.sidebar-menu .el-menu-item .el-icon {
  color: var(--sidebar-icon);
  font-size: 16px;
  transition: color 0.2s;
}

.sidebar-menu .el-menu-item:hover {
  background: var(--sidebar-item-hover);
  color: var(--sidebar-text-active);
}

.sidebar-menu .el-menu-item.is-active {
  background: var(--sidebar-item-active);
  color: var(--sidebar-text-active);
  border-color: rgba(99,102,241,0.3);
}

.sidebar-menu .el-menu-item.is-active .el-icon {
  color: var(--sidebar-icon-active);
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--sidebar-border);
}

.version-tag {
  display: inline-block;
  font-size: 10px;
  font-weight: 600;
  color: rgba(255,255,255,0.25);
  background: rgba(255,255,255,0.05);
  padding: 3px 8px;
  border-radius: 4px;
  letter-spacing: 0.05em;
}

/* ====== 主内容区 ====== */
.main-panel {
  padding: 24px;
  overflow-y: auto;
  background: var(--bg-page);
}

/* ====== 通用卡片 ====== */
.card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-sm);
  border: 1px solid rgba(0,0,0,0.04);
  transition: box-shadow 0.2s ease;
}

.card:hover {
  box-shadow: var(--shadow-md);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f1f5f9;
}

.card-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ====== 状态标签 ====== */
.status-tag {
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11.5px;
  font-weight: 600;
  letter-spacing: 0.01em;
}

.status-new      { background: #dbeafe; color: #2563eb; }
.status-contacted { background: #fef3c7; color: #d97706; }
.status-replied  { background: #d1fae5; color: #059669; }
.status-interested { background: #d1fae5; color: #059669; }
.status-quoted   { background: #d1fae5; color: #059669; }
.status-closed   { background: #f1f5f9; color: #64748b; }
.status-invalid   { background: #fee2e2; color: #dc2626; }
.status-blacklist { background: #dc2626; color: white; }

/* ====== AI等级 ====== */
.level-a { color: #059669; font-weight: 700; }
.level-b { color: #2563eb; font-weight: 700; }
.level-c { color: #d97706; font-weight: 700; }
.level-d { color: #dc2626; font-weight: 700; }

/* ====== 列表页 ====== */
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filter-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

/* ====== 通用按钮增强 ====== */
.el-button--primary {
  background: var(--accent-gradient) !important;
  border: none !important;
  box-shadow: 0 2px 8px rgba(99,102,241,0.25) !important;
}

.el-button--primary:hover {
  box-shadow: 0 4px 16px rgba(99,102,241,0.35) !important;
  transform: translateY(-1px);
}

/* ====== 表格美化 ====== */
.el-table {
  --el-table-border-color: #f1f5f9;
  --el-table-header-bg-color: #f8fafc;
  border-radius: var(--radius-md);
  overflow: hidden;
}

.el-table th.el-table__cell {
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.el-table tr:hover > td {
  background: #f8fafc !important;
}

/* ====== 滚动条美化 ====== */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.12);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(0,0,0,0.2);
}

/* ====== 响应式 ====== */
@media (max-width: 1024px) {
  .aside-panel {
    width: 200px !important;
  }
}
</style>
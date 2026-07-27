<template>
  <div class="app-container">
    <el-container>
      <!-- 侧边栏 (桌面端) -->
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
        <!-- 顶部栏 -->
        <div class="top-header" v-if="showLayout">
          <div class="top-header-left">
            <span class="mobile-logo">🛒 Buyer Radar</span>
          </div>
          <div class="top-header-right">
            <el-dropdown trigger="click" @command="handleUserCommand">
              <span class="user-info">
                <el-icon><UserFilled /></el-icon>
                <span class="username">{{ currentUsername }}</span>
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="password">修改密码</el-dropdown-item>
                  <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        <router-view />
      </el-main>
    </el-container>

    <!-- 移动端底部导航 -->
    <nav class="mobile-nav" v-if="showLayout">
      <router-link to="/" class="nav-item" :class="{ active: activeMenu === '/' }">
        <el-icon><HomeFilled /></el-icon>
        <span>首页</span>
      </router-link>
      <router-link to="/buyers" class="nav-item" :class="{ active: activeMenu === '/buyers' }">
        <el-icon><User /></el-icon>
        <span>客户</span>
      </router-link>
      <router-link to="/search" class="nav-item" :class="{ active: activeMenu === '/search' }">
        <el-icon><Search /></el-icon>
        <span>搜索</span>
      </router-link>
      <router-link to="/import" class="nav-item" :class="{ active: activeMenu === '/import' }">
        <el-icon><Upload /></el-icon>
        <span>导入</span>
      </router-link>
      <router-link to="/settings" class="nav-item" :class="{ active: activeMenu === '/settings' }">
        <el-icon><Setting /></el-icon>
        <span>设置</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { HomeFilled, User, Upload, Search, ChatDotRound, Message, Download, Setting, UserFilled, ArrowDown } from '@element-plus/icons-vue'
import { authAPI } from './services/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const activeMenu = computed(() => route.path)
const showLayout = computed(() => route.path !== '/login')
const currentUsername = ref(localStorage.getItem('username') || '用户')

async function handleUserCommand(command) {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      try {
        await authAPI.logout()
      } catch (e) {
        // 即使logout接口失败也清除本地token
      }
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      router.push('/login')
    } catch (e) {
      // 用户取消
    }
  } else if (command === 'password') {
    ElMessage.info('修改密码功能开发中')
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  /* 商务简洁：白色侧栏 + 细边框 + 柔和阴影 */
  --sidebar-bg: #ffffff;
  --sidebar-border: #e8eaed;
  --sidebar-item-hover: #f5f6f8;
  --sidebar-item-active: #eef4ff;
  --sidebar-item-active-border: #2563eb;
  --sidebar-text: #5f6b7a;
  --sidebar-text-active: #1a2332;
  --sidebar-icon: #8a94a3;
  --sidebar-icon-active: #2563eb;
  --accent-primary: #2563eb;
  --accent-primary-hover: #1d4ed8;
  --accent-soft: #eef4ff;
  --bg-page: #f5f6f8;
  --bg-card: #ffffff;
  --border-color: #e8eaed;
  --text-primary: #1a2332;
  --text-secondary: #5f6b7a;
  --shadow-sm: 0 1px 2px rgba(16,24,40,0.04);
  --shadow-md: 0 2px 8px rgba(16,24,40,0.06);
  --shadow-lg: 0 8px 24px rgba(16,24,40,0.08);
  --radius-lg: 12px;
  --radius-md: 10px;
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
  background: var(--accent-soft);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.logo-text h2 {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
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
  border-color: #cfe0ff;
  font-weight: 600;
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
  color: #9aa3af;
  background: #f5f6f8;
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

/* ====== 顶部栏 ====== */
.top-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
}

.top-header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 8px;
  transition: background 0.2s;
  color: #475569;
  font-size: 13.5px;
  font-weight: 500;
}

.user-info:hover {
  background: #f1f5f9;
}

.user-info .username {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ====== 通用卡片 ====== */
.card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
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
  background: var(--accent-primary) !important;
  border: 1px solid var(--accent-primary) !important;
  box-shadow: none !important;
}

.el-button--primary:hover,
.el-button--primary:focus {
  background: var(--accent-primary-hover) !important;
  border-color: var(--accent-primary-hover) !important;
  box-shadow: none !important;
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
.mobile-logo {
  display: none;
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.mobile-nav {
  display: none;
}

@media (max-width: 1024px) {
  .aside-panel {
    width: 200px !important;
  }
}

@media (max-width: 768px) {
  .app-container {
    height: auto;
    min-height: 100vh;
    overflow: visible;
  }

  .app-container .el-container {
    flex-direction: column;
  }

  .aside-panel {
    display: none !important;
  }

  .main-panel {
    padding: 12px;
    padding-bottom: 72px;
    overflow: visible;
  }

  .mobile-logo {
    display: block;
  }

  .top-header {
    margin-bottom: 12px;
    padding-bottom: 10px;
  }

  .card {
    padding: 16px;
    margin-bottom: 12px;
    border-radius: 12px;
  }

  .card-header {
    margin-bottom: 12px;
    padding-bottom: 10px;
  }

  /* 底部导航栏 */
  .mobile-nav {
    display: flex;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 60px;
    background: #fff;
    border-top: 1px solid #e2e8f0;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.06);
    z-index: 1000;
    padding-bottom: env(safe-area-inset-bottom, 0);
  }

  .mobile-nav .nav-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    text-decoration: none;
    color: #94a3b8;
    font-size: 10px;
    font-weight: 500;
    transition: color 0.2s;
  }

  .mobile-nav .nav-item .el-icon {
    font-size: 20px;
  }

  .mobile-nav .nav-item.active {
    color: var(--accent-primary);
  }

  /* 表格横向滚动 */
  .el-table {
    font-size: 12px;
  }

  /* 分页简化 */
  .pagination-wrap .el-pagination,
  .pagination .el-pagination {
    justify-content: center;
  }

  .el-pagination .el-pagination__sizes,
  .el-pagination .el-pagination__jump {
    display: none !important;
  }

  /* 筛选栏 */
  .filter-bar {
    gap: 8px;
  }

  .filter-row {
    flex-direction: column;
    gap: 8px;
  }

  .filter-row .el-select {
    width: 100%;
  }

  /* 弹窗适配 */
  .el-dialog {
    width: 92vw !important;
    margin: 5vh auto !important;
  }

  .el-dialog__body {
    padding: 12px 16px;
  }
}
</style>
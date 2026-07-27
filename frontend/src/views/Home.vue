<template>
  <div class="home">
    <!-- Hero 区域 -->
    <div class="hero-section">
      <div class="hero-bg-decoration"></div>
      <div class="hero-content">
        <div class="hero-badge">
          <span class="pulse-dot"></span>
          AI驱动 · 智能获客
        </div>
        <h1>AI Buyer Radar</h1>
        <p class="hero-subtitle">AI海外采购商雷达系统</p>
        <p class="hero-desc">输入产品关键词 + 国家，自动发现真实海外采购商</p>
        <div class="quick-actions">
          <el-button type="primary" size="large" @click="$router.push('/import')">
            <el-icon><Upload /></el-icon>
            导入数据
          </el-button>
          <el-button size="large" @click="$router.push('/search')">
            <el-icon><Search /></el-icon>
            智能搜索
          </el-button>
          <el-button size="large" @click="$router.push('/buyers')">
            <el-icon><User /></el-icon>
            查看列表
          </el-button>
        </div>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-if="loadError && !loading" class="error-state card">
      <el-icon :size="48" color="#94a3b8"><WarningFilled /></el-icon>
      <h3>数据暂时无法加载</h3>
      <p>请检查网络连接或稍后重试</p>
      <el-button type="primary" @click="retryData">重新加载</el-button>
    </div>

    <!-- 空数据引导 -->
    <div v-else-if="!loading && !loadError && (stats.total_buyers === 0)" class="empty-state card">
      <el-icon :size="48" color="#94a3b8"><FolderOpened /></el-icon>
      <h3>还没有采购商数据</h3>
      <p>开始搜索新商户，或导入已有客户名单</p>
      <div class="empty-actions">
        <el-button type="primary" @click="$router.push('/search')">搜索第一个市场</el-button>
        <el-button @click="$router.push('/import')">导入客户名单</el-button>
      </div>
    </div>

    <!-- 正常内容 -->
    <template v-else>
      <!-- 统计卡片 -->
      <div class="stats-grid" v-loading="loading">
        <div class="stat-card" v-for="(stat, idx) in statCards" :key="idx" :style="{ '--delay': idx * 0.1 + 's' }">
          <div class="stat-glow" :style="{ background: stat.glow }"></div>
          <div class="stat-icon-wrap" :style="{ background: stat.bg }">
            <el-icon size="22" :style="{ color: stat.color }">
              <component :is="stat.icon" />
            </el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
          <div class="stat-trend" v-if="stat.trend">
            <el-icon><Top /></el-icon>
            {{ stat.trend }}
          </div>
        </div>
      </div>

      <!-- 图表 + 信息区域 -->
      <div class="charts-row">
        <!-- 状态分布图 -->
        <div class="card chart-card">
          <div class="card-header">
            <h3>
              <span class="card-icon">📈</span>
              采购商状态分布
            </h3>
          </div>
          <div ref="statusChartRef" class="chart-container" v-loading="loading"></div>
        </div>

        <!-- 国家分布图 -->
        <div class="card chart-card">
          <div class="card-header">
            <h3>
              <span class="card-icon">🌍</span>
              国家分布 TOP5
            </h3>
          </div>
          <div ref="countryChartRef" class="chart-container" v-loading="loading"></div>
        </div>

        <!-- AI等级分布 -->
        <div class="card chart-card">
          <div class="card-header">
            <h3>
              <span class="card-icon">🏆</span>
              AI等级分布
            </h3>
          </div>
          <div ref="levelChartRef" class="chart-container" v-loading="loading"></div>
        </div>
      </div>

      <!-- 最近采购商列表 -->
      <div class="card">
        <div class="card-header">
          <h3>
            <span class="card-icon">🛒</span>
            最近添加的采购商
          </h3>
          <el-button text @click="$router.push('/buyers')">
            查看全部 <el-icon><Right /></el-icon>
          </el-button>
        </div>
        <div class="recent-list" v-if="recentBuyers.length">
          <div class="recent-item" v-for="buyer in recentBuyers" :key="buyer.id" @click="$router.push(`/buyers/${buyer.id}`)">
            <div class="recent-avatar" :style="{ background: getAvatarBg(buyer.company_name) }">
              {{ getInitials(buyer.company_name) }}
            </div>
            <div class="recent-info">
              <div class="recent-name">{{ buyer.company_name }}</div>
              <div class="recent-meta">{{ buyer.country }} · {{ buyer.industry || '未知行业' }}</div>
            </div>
            <div class="recent-right">
              <el-tag :type="levelType(buyer.ai_level)" size="small" effect="plain">
                {{ buyer.ai_level || 'C' }}级
              </el-tag>
              <span :class="`status-tag status-${buyer.status}`">{{ statusLabel(buyer.status) }}</span>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无数据，开始导入你的第一个采购商吧" />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { buyersAPI } from '../services/api'
import { User, Star, Message, Warning, Upload, Search, PriceTag, Top, Right, WarningFilled, FolderOpened } from '@element-plus/icons-vue'

const loading = ref(true)
const loadError = ref(false)
const stats = ref({})
const recentBuyers = ref([])
const statusChartRef = ref(null)
const countryChartRef = ref(null)
const levelChartRef = ref(null)

let statusChart = null
let countryChart = null
let levelChart = null

const statusLabels = {
  new: '新增',
  contacted: '已联系',
  replied: '已回复',
  interested: '有意向',
  quoted: '已报价',
  closed: '已成交',
  invalid: '无效',
  blacklist: '黑名单'
}

const statusColors = {
  new: '#3b82f6',
  contacted: '#f59e0b',
  replied: '#10b981',
  interested: '#10b981',
  quoted: '#10b981',
  closed: '#94a3b8',
  invalid: '#ef4444',
  blacklist: '#ef4444'
}

const levelColors = { A: '#10b981', B: '#3b82f6', C: '#f59e0b', D: '#ef4444' }

function statusLabel(status) { return statusLabels[status] || status }
function levelType(level) {
  const map = { A: 'success', B: '', C: 'warning', D: 'danger' }
  return map[level] || ''
}

function getInitials(name) {
  if (!name) return '?'
  return name.slice(0, 2).toUpperCase()
}

const avatarColors = ['#2563eb', '#0d9488', '#4f46e5', '#d97706', '#0891b2', '#475569']
function getAvatarBg(name) {
  if (!name) return avatarColors[0]
  const idx = name.charCodeAt(0) % avatarColors.length
  return avatarColors[idx]
}

const statCards = computed(() => [
  {
    icon: User,
    label: '采购商总数',
    value: stats.value.total_buyers || 0,
    bg: 'linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)',
    color: '#2563eb',
    glow: 'radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%)',
    trend: null
  },
  {
    icon: Star,
    label: 'A级采购商',
    value: stats.value.by_level?.A || 0,
    bg: 'linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)',
    color: '#059669',
    glow: 'radial-gradient(circle, rgba(5,150,105,0.15) 0%, transparent 70%)',
    trend: null
  },
  {
    icon: Message,
    label: '已联系',
    value: stats.value.by_status?.contacted || 0,
    bg: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
    color: '#d97706',
    glow: 'radial-gradient(circle, rgba(217,119,6,0.15) 0%, transparent 70%)',
    trend: null
  },
  {
    icon: Warning,
    label: '平均AI评分',
    value: (stats.value.avg_ai_score || 0).toFixed(1),
    bg: 'linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)',
    color: '#dc2626',
    glow: 'radial-gradient(circle, rgba(220,38,38,0.15) 0%, transparent 70%)',
    trend: null
  }
])

async function fetchData() {
  loading.value = true
  loadError.value = false
  try {
    const data = await buyersAPI.stats()
    stats.value = data
    recentBuyers.value = data.recent_buyers || []
  } catch (e) {
    console.error(e)
    loadError.value = true
  } finally {
    loading.value = false
  }
}

async function retryData() {
  await fetchData()
  if (!loadError.value) {
    await nextTick()
    initCharts()
  }
}

function initCharts() {
  if (!statusChartRef.value) return

  // 状态饼图
  statusChart = echarts.init(statusChartRef.value)
  const statusData = Object.entries(stats.value.by_status || {}).map(([name, value]) => ({
    name: statusLabels[name] || name,
    value,
    itemStyle: { color: statusColors[name] || '#94a3b8' }
  }))
  statusChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, left: 'center', textStyle: { fontSize: 12 } },
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
      data: statusData
    }]
  })

  // 国家柱状图
  countryChart = echarts.init(countryChartRef.value)
  const topCountries = (stats.value.top_countries || []).slice(0, 5)
  countryChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 10, right: 10, bottom: 10, top: 10, containLabel: true },
    xAxis: { type: 'category', data: topCountries.map(c => c.country), axisLabel: { fontSize: 11 } },
    yAxis: { type: 'value', axisLabel: { fontSize: 10 }, splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } } },
    series: [{
      type: 'bar',
      data: topCountries.map((c, i) => ({
        value: c.cnt,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#3b82f6' },
            { offset: 1, color: '#2563eb' }
          ]),
          borderRadius: [6, 6, 0, 0]
        }
      })),
      barMaxWidth: 32
    }]
  })

  // 等级雷达/环形图
  levelChart = echarts.init(levelChartRef.value)
  const levelData = ['A', 'B', 'C', 'D'].map(level => ({
    name: level + '级',
    value: stats.value.by_level?.[level] || 0,
    itemStyle: { color: levelColors[level] }
  }))
  levelChart.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['50%', '75%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { formatter: '{b}\n{c}', fontSize: 12 },
      emphasis: { label: { fontSize: 14, fontWeight: 'bold' } },
      data: levelData
    }]
  })
}

onMounted(async () => {
  await fetchData()
  await nextTick()
  initCharts()
})

onUnmounted(() => {
  statusChart?.dispose()
  countryChart?.dispose()
  levelChart?.dispose()
})
</script>

<style scoped>
.home {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ====== Hero ====== */
.hero-section {
  position: relative;
  border-radius: 16px;
  padding: 44px 40px;
  overflow: hidden;
  background: #ffffff;
  border: 1px solid #e8eaed;
  box-shadow: 0 1px 2px rgba(16,24,40,0.04);
  color: #1a2332;
}

.hero-bg-decoration {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 15% 50%, rgba(37,99,235,0.06) 0%, transparent 55%),
    radial-gradient(ellipse at 85% 15%, rgba(37,99,235,0.05) 0%, transparent 50%);
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 1;
  text-align: center;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #2563eb;
  background: #eef4ff;
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid #dbe7ff;
  margin-bottom: 20px;
  letter-spacing: 0.03em;
}

.pulse-dot {
  width: 7px;
  height: 7px;
  background: #10b981;
  border-radius: 50%;
  box-shadow: 0 0 0 3px rgba(16,185,129,0.2);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 3px rgba(16,185,129,0.2); }
  50% { box-shadow: 0 0 0 6px rgba(16,185,129,0.08); }
}

.hero-content h1 {
  font-size: 40px;
  font-weight: 800;
  letter-spacing: -0.03em;
  margin-bottom: 8px;
  color: #1a2332;
}

.hero-subtitle {
  font-size: 18px;
  font-weight: 500;
  color: #475569;
  margin-bottom: 8px;
}

.hero-desc {
  font-size: 14px;
  color: #8a94a3;
  margin-bottom: 32px;
}

.quick-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.quick-actions .el-button {
  padding: 12px 28px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 10px;
  transition: all 0.2s;
}

/* ====== 统计卡片 ====== */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  position: relative;
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 1px 2px rgba(16,24,40,0.04);
  border: 1px solid #e8eaed;
  overflow: hidden;
  transition: box-shadow 0.2s ease;
  animation: slideUp 0.4s ease both;
  animation-delay: var(--delay, 0s);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.stat-card:hover {
  box-shadow: 0 2px 8px rgba(16,24,40,0.06);
}

.stat-glow {
  display: none;
}

.stat-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-body {
  flex: 1;
}

.stat-value {
  font-size: 30px;
  font-weight: 800;
  color: #0f172a;
  line-height: 1;
  letter-spacing: -0.02em;
}

.stat-label {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
  margin-top: 4px;
}

.stat-trend {
  font-size: 11px;
  color: #10b981;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 2px;
}

/* ====== 图表区域 ====== */
.charts-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.chart-card {
  padding: 20px;
}

.chart-container {
  height: 220px;
  width: 100%;
}

/* ====== 最近列表 ====== */
.recent-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 4px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;
}

.recent-item:hover {
  background: #f8fafc;
}

.recent-avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
}

.recent-info {
  flex: 1;
  min-width: 0;
}

.recent-name {
  font-size: 13.5px;
  font-weight: 600;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.recent-meta {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 2px;
}

.recent-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

/* ====== 响应式 ====== */
@media (max-width: 1200px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .charts-row { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .hero-section { padding: 28px 16px; border-radius: 14px; }
  .hero-content h1 { font-size: 24px; }
  .hero-subtitle { font-size: 14px; }
  .hero-desc { font-size: 12px; margin-bottom: 20px; }
  .quick-actions { flex-direction: column; gap: 8px; }
  .quick-actions .el-button { width: 100%; padding: 10px 20px; }
  .stats-grid { grid-template-columns: 1fr 1fr; gap: 10px; }
  .stat-card { padding: 14px; gap: 10px; }
  .stat-value { font-size: 22px; }
  .stat-icon-wrap { width: 38px; height: 38px; }
  .charts-row { grid-template-columns: 1fr; gap: 12px; }
  .chart-container { height: 180px; }
  .recent-item { padding: 10px 2px; }
  .recent-name { font-size: 13px; }
}

@media (max-width: 480px) {
  .stats-grid { grid-template-columns: 1fr; }
  .hero-content h1 { font-size: 20px; }
}

/* ====== 错误/空状态 ====== */
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  text-align: center;
}

.error-state h3,
.empty-state h3 {
  font-size: 18px;
  font-weight: 600;
  color: #334155;
  margin: 16px 0 8px;
}

.error-state p,
.empty-state p {
  font-size: 14px;
  color: #94a3b8;
  margin-bottom: 24px;
}

.empty-actions {
  display: flex;
  gap: 12px;
}
</style>
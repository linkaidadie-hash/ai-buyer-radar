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
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { buyersAPI } from '../services/api'
import { User, Star, Message, Warning, Upload, Search, PriceTag, Top, Right } from '@element-plus/icons-vue'

// 动态引入 echarts（懒加载避免打包体积问题）
let echarts = null

const loading = ref(true)
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

const avatarColors = ['#6366f1', '#8b5cf6', '#ec4899', '#14b8a6', '#f59e0b', '#3b82f6']
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
  try {
    const data = await buyersAPI.stats()
    stats.value = data
    recentBuyers.value = data.recent_buyers || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function initCharts() {
  if (!echarts || !statusChartRef.value) return

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
            { offset: 0, color: '#6366f1' },
            { offset: 1, color: '#8b5cf6' }
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
  try {
    echarts = (await import('echarts')).default
  } catch (e) {
    console.warn('echarts not available:', e)
  }

  await fetchData()

  await new Promise(r => setTimeout(r, 100))
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
  border-radius: 20px;
  padding: 48px 40px;
  overflow: hidden;
  background: linear-gradient(135deg, #0f1623 0%, #1e293b 100%);
  color: white;
}

.hero-bg-decoration {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 20% 50%, rgba(99,102,241,0.25) 0%, transparent 60%),
    radial-gradient(ellipse at 80% 20%, rgba(139,92,246,0.2) 0%, transparent 50%);
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
  color: rgba(255,255,255,0.7);
  background: rgba(255,255,255,0.08);
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,0.1);
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
  font-size: 42px;
  font-weight: 800;
  letter-spacing: -0.03em;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #ffffff 0%, #c7d2fe 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-subtitle {
  font-size: 18px;
  font-weight: 500;
  opacity: 0.85;
  margin-bottom: 8px;
}

.hero-desc {
  font-size: 14px;
  opacity: 0.5;
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
  border-radius: 16px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.03);
  border: 1px solid rgba(0,0,0,0.04);
  overflow: hidden;
  transition: all 0.25s ease;
  animation: slideUp 0.4s ease both;
  animation-delay: var(--delay, 0s);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.stat-card:hover {
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.stat-glow {
  position: absolute;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  top: -40px;
  right: -30px;
  pointer-events: none;
  filter: blur(30px);
}

.stat-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
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

@media (max-width: 640px) {
  .hero-section { padding: 32px 20px; }
  .hero-content h1 { font-size: 28px; }
  .stats-grid { grid-template-columns: 1fr 1fr; gap: 12px; }
  .stat-value { font-size: 24px; }
}
</style>
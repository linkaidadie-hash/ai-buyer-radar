<template>
  <div class="buyers-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-title-wrap">
        <h2>采购商列表</h2>
        <span class="total-badge">{{ pagination.total }} 条记录</span>
      </div>
      <div class="actions">
        <el-button type="primary" @click="$router.push('/import')">
          <el-icon><Upload /></el-icon>
          导入
        </el-button>
        <el-button @click="exportCSV">
          <el-icon><Download /></el-icon>
          导出
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="card filter-card">
      <div class="filter-row">
        <el-input
          v-model="filters.search"
          placeholder="搜索公司 / 产品 / 行业..."
          clearable
          size="large"
          class="search-input"
          @clear="loadData"
          @keyup.enter="loadData"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select v-model="filters.country" placeholder="国家" clearable size="large" @change="loadData">
          <template #prefix><el-icon><MapLocation /></el-icon></template>
          <el-option v-for="c in countries" :key="c.country" :label="c.country" :value="c.country" />
        </el-select>

        <el-select v-model="filters.status" placeholder="状态" clearable size="large" @change="loadData">
          <template #prefix><el-icon><CircleCheck /></el-icon></template>
          <el-option v-for="s in statusOptions" :key="s.value" :label="s.label" :value="s.value" />
        </el-select>

        <el-select v-model="filters.ai_level" placeholder="AI等级" clearable size="large" @change="loadData">
          <template #prefix><el-icon><Star /></el-icon></template>
          <el-option label="A级" value="A" />
          <el-option label="B级" value="B" />
          <el-option label="C级" value="C" />
          <el-option label="D级" value="D" />
        </el-select>

        <el-select v-model="filters.source" placeholder="数据源" clearable size="large" @change="loadData">
          <template #prefix><el-icon><Connection /></el-icon></template>
          <el-option v-for="s in sources" :key="s.source" :label="s.source" :value="s.source" />
        </el-select>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-if="loadError && !loading" class="card error-state">
      <el-icon :size="48" color="#94a3b8"><WarningFilled /></el-icon>
      <h3>数据加载失败</h3>
      <p>请检查网络连接或稍后重试</p>
      <el-button type="primary" @click="loadData">重新加载</el-button>
    </div>

    <!-- 空数据引导 -->
    <div v-else-if="!loading && !loadError && pagination.total === 0 && buyers.length === 0" class="card empty-state">
      <el-icon :size="48" color="#94a3b8"><FolderOpened /></el-icon>
      <h3>开始搜索您的第一个海外采购商</h3>
      <p>搜索新商户，或导入已有客户数据</p>
      <div class="empty-actions">
        <el-button type="primary" @click="$router.push('/search')">搜索新商户</el-button>
        <el-button @click="$router.push('/import')">导入客户数据</el-button>
      </div>
    </div>

    <!-- 表格 -->
    <div v-else class="card table-card" v-loading="loading">
      <el-table
        :data="buyers"
        @row-click="viewDetail"
        :row-class-name="tableRowClassName"
        stripe
      >
        <el-table-column type="index" width="60" label="#" align="center" />

        <el-table-column prop="company_name" label="公司名称" min-width="200" fixed>
          <template #default="{ row }">
            <div class="company-cell">
              <div class="company-avatar" :style="{ background: getAvatarBg(row.company_name) }">
                {{ getInitials(row.company_name) }}
              </div>
              <div class="company-info">
                <div class="company-name">{{ row.company_name }}</div>
                <div class="company-country" v-if="row.country">
                  <el-icon><Location /></el-icon> {{ row.country }}
                </div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="industry" label="行业" width="140">
          <template #default="{ row }">
            <span class="industry-tag">{{ row.industry || '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="ai_score" label="评分" width="100" align="center">
          <template #default="{ row }">
            <div class="score-wrap">
              <span class="score-num" :class="`level-${row.ai_level?.toLowerCase()}`">
                {{ row.ai_score != null ? row.ai_score.toFixed(1) : '—' }}
              </span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="ai_level" label="等级" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="levelType(row.ai_level)" size="small" effect="plain" round>
              {{ row.ai_level || 'C' }}级
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="110" align="center">
          <template #default="{ row }">
            <span :class="`status-tag status-${row.status}`">{{ statusLabel(row.status) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="source" label="来源" width="120">
          <template #default="{ row }">
            <span class="source-chip">{{ row.source || '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="添加时间" width="120">
          <template #default="{ row }">
            <span class="date-text">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="" width="60" align="center" fixed="right">
          <template #default="{ row }">
            <el-icon class="row-arrow"><Right /></el-icon>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @current-change="loadData"
          @size-change="loadData"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { buyersAPI, searchAPI, exportAPI } from '../services/api'
import { ElMessage } from 'element-plus'
import { Upload, Download, Search, Right, MapLocation, CircleCheck, Star, Connection, Location, WarningFilled, FolderOpened } from '@element-plus/icons-vue'

const router = useRouter()
const loading = ref(false)
const loadError = ref(false)
const buyers = ref([])
const countries = ref([])
const sources = ref([])

const filters = ref({
  search: '',
  country: '',
  status: '',
  ai_level: '',
  source: ''
})

const pagination = ref({
  page: 1,
  page_size: 20,
  total: 0
})

const statusOptions = [
  { value: 'new', label: '新增' },
  { value: 'contacted', label: '已联系' },
  { value: 'replied', label: '已回复' },
  { value: 'interested', label: '有意向' },
  { value: 'quoted', label: '已报价' },
  { value: 'closed', label: '已成交' },
  { value: 'invalid', label: '无效' },
  { value: 'blacklist', label: '黑名单' }
]

const statusLabels = {
  new: '新增', contacted: '已联系', replied: '已回复',
  interested: '有意向', quoted: '已报价', closed: '已成交',
  invalid: '无效', blacklist: '黑名单'
}

const avatarColors = ['#2563eb', '#0d9488', '#4f46e5', '#d97706', '#0891b2', '#475569', '#059669']

function statusLabel(status) { return statusLabels[status] || status }

function levelType(level) {
  return { A: 'success', B: '', C: 'warning', D: 'danger' }[level] || 'info'
}

function getInitials(name) {
  if (!name) return '?'
  return name.slice(0, 2).toUpperCase()
}

function getAvatarBg(name) {
  if (!name) return avatarColors[0]
  return avatarColors[name.charCodeAt(0) % avatarColors.length]
}

function formatDate(date) {
  if (!date) return '-'
  return date.split(' ')[0]
}

function tableRowClassName({ row }) {
  return 'buyer-row'
}

async function loadData() {
  loading.value = true
  loadError.value = false
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.page_size,
      ...Object.fromEntries(Object.entries(filters.value).filter(([, v]) => v !== ''))
    }
    const res = await buyersAPI.list(params)
    buyers.value = res.data || []
    pagination.value.total = res.total || 0
  } catch (e) {
    console.error(e)
    loadError.value = true
  } finally {
    loading.value = false
  }
}

async function loadFilters() {
  try {
    const [cr, sr] = await Promise.all([searchAPI.countries(), searchAPI.sources()])
    countries.value = cr
    sources.value = sr
  } catch (e) {
    console.error(e)
  }
}

function viewDetail(row) {
  router.push(`/buyers/${row.id}`)
}

async function exportCSV() {
  try {
    await exportAPI.csv(filters.value)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

onMounted(() => {
  loadData()
  loadFilters()
})
</script>

<style scoped>
.buyers-page {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ====== 页面标题 ====== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title-wrap h2 {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}

.total-badge {
  font-size: 12px;
  font-weight: 600;
  color: #2563eb;
  background: #eef4ff;
  padding: 3px 10px;
  border-radius: 20px;
}

.actions {
  display: flex;
  gap: 8px;
}

/* ====== 筛选栏 ====== */
.filter-card {
  padding: 16px 20px;
}

.filter-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}

.search-input {
  flex: 1;
  min-width: 200px;
}

/* ====== 表格卡片 ====== */
.table-card {
  padding: 0;
  overflow: hidden;
}

/* ====== 表格单元格 ====== */
.company-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.company-avatar {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
}

.company-info {
  min-width: 0;
}

.company-name {
  font-size: 13.5px;
  font-weight: 600;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
}

.company-country {
  font-size: 11px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 2px;
  margin-top: 1px;
}

.industry-tag {
  font-size: 12px;
  color: #64748b;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 4px;
}

.score-wrap {
  display: flex;
  justify-content: center;
}

.score-num {
  font-size: 14px;
  font-weight: 700;
}

.level-a { color: #059669; }
.level-b { color: #2563eb; }
.level-c { color: #d97706; }
.level-d { color: #dc2626; }

.source-chip {
  font-size: 11.5px;
  color: #64748b;
  background: #f8fafc;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid #f1f5f9;
}

.date-text {
  font-size: 12px;
  color: #94a3b8;
}

.row-arrow {
  color: #cbd5e1;
  transition: transform 0.2s;
}

:deep(.buyer-row):hover .row-arrow {
  transform: translateX(3px);
  color: #2563eb;
}

/* ====== 分页 ====== */
.pagination-wrap {
  padding: 16px 20px;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #f1f5f9;
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

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .filter-row {
    flex-direction: column;
  }

  .search-input {
    min-width: 100%;
  }

  .filter-row .el-select {
    width: 100%;
  }

  .company-name {
    max-width: 120px;
  }

  .pagination-wrap {
    justify-content: center;
    padding: 12px;
  }

  .empty-actions {
    flex-direction: column;
    width: 100%;
  }

  .empty-actions .el-button {
    width: 100%;
  }
}
</style>
<template>
  <div class="crm-page">
    <h2>CRM跟进</h2>

    <div class="tabs-bar">
      <el-radio-group v-model="activeTab" size="default">
        <el-radio-button label="followup">待跟进</el-radio-button>
        <el-radio-button label="recent">最近跟进</el-radio-button>
        <el-radio-button label="all">全部采购商</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 待跟进 -->
    <div v-if="activeTab === 'followup'" class="card" v-loading="loading">
      <div v-if="followupDue.length > 0">
        <el-table :data="followupDue">
          <el-table-column prop="company_name" label="公司" min-width="180" />
          <el-table-column prop="country" label="国家" width="100" />
          <el-table-column prop="ai_score" label="AI评分" width="80">
            <template #default="{ row }">
              <span :class="`level-${row.ai_level?.toLowerCase()}`">{{ row.ai_score }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="followup_date" label="计划跟进" width="100">
            <template #default="{ row }">
              <span :class="{ 'overdue': isOverdue(row.followup_date) }">
                {{ row.followup_date }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="next_followup" label="下次跟进" width="120" />
          <el-table-column prop="result" label="上次结果" width="90" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" type="primary" @click="goToDetail(row.id)">跟进</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-empty v-else description="暂无待跟进记录" />
    </div>

    <!-- 最近跟进 -->
    <div v-if="activeTab === 'recent'" class="card" v-loading="loading">
      <div v-if="recentFollowups.length > 0">
        <el-table :data="recentFollowups">
          <el-table-column prop="company_name" label="公司" min-width="180">
            <template #default="{ row }">
              <router-link :to="`/buyers/${row.id}`">{{ row.company_name }}</router-link>
            </template>
          </el-table-column>
          <el-table-column prop="country" label="国家" width="100" />
          <el-table-column prop="ai_score" label="评分" width="60" />
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <span :class="`status-tag status-${row.status}`">{{ statusLabel(row.status) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="添加时间" width="100">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button size="small" @click="goToDetail(row.id)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-empty v-else description="暂无跟进记录" />
    </div>

    <!-- 全部采购商 -->
    <div v-if="activeTab === 'all'" class="card" v-loading="loading">
      <div class="filter-bar">
        <el-select v-model="filterStatus" placeholder="状态筛选" clearable @change="loadAll">
          <el-option label="新增" value="new" />
          <el-option label="已联系" value="contacted" />
          <el-option label="已回复" value="replied" />
          <el-option label="有意向" value="interested" />
          <el-option label="已报价" value="quoted" />
          <el-option label="已成交" value="closed" />
          <el-option label="无效" value="invalid" />
        </el-select>
        <el-select v-model="filterLevel" placeholder="等级筛选" clearable @change="loadAll">
          <el-option label="A级" value="A" />
          <el-option label="B级" value="B" />
          <el-option label="C级" value="C" />
          <el-option label="D级" value="D" />
        </el-select>
      </div>
      <el-table :data="allBuyers" @row-click="goToDetail">
        <el-table-column prop="company_name" label="公司" min-width="180" />
        <el-table-column prop="country" label="国家" width="100" />
        <el-table-column prop="ai_score" label="评分" width="60" />
        <el-table-column prop="ai_level" label="等级" width="60">
          <template #default="{ row }">
            <el-tag :type="levelType(row.ai_level)" size="small">{{ row.ai_level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <span :class="`status-tag status-${row.status}`">{{ statusLabel(row.status) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="140" />
      </el-table>
      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          :total="total"
          :page-size="20"
          layout="total, prev, pager, next"
          @current-change="loadAll"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { buyersAPI } from '../services/api'

const router = useRouter()
const loading = ref(false)
const activeTab = ref('followup')
const followupDue = ref([])
const recentFollowups = ref([])
const allBuyers = ref([])
const total = ref(0)
const page = ref(1)
const filterStatus = ref('')
const filterLevel = ref('')

function statusLabel(status) {
  const labels = { new: '新增', contacted: '已联系', replied: '已回复', interested: '有意向', quoted: '已报价', closed: '已成交', invalid: '无效' }
  return labels[status] || status
}

function levelType(level) {
  return { A: 'success', B: 'primary', C: 'warning', D: 'danger' }[level] || 'info'
}

function formatDate(date) {
  return date ? date.split(' ')[0] : '-'
}

function isOverdue(date) {
  if (!date) return false
  return new Date(date) < new Date()
}

function goToDetail(row) {
  router.push(`/buyers/${row.id}`)
}

async function loadFollowupDue() {
  loading.value = true
  try {
    const res = await buyersAPI.stats()
    // 简化处理，实际应调用专门的接口
    followupDue.value = []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadAll() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: 20 }
    if (filterStatus.value) params.status = filterStatus.value
    if (filterLevel.value) params.ai_level = filterLevel.value
    const res = await buyersAPI.list(params)
    allBuyers.value = res.data
    total.value = res.total
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAll()
})
</script>

<style scoped>
.tabs-bar {
  margin-bottom: 20px;
}

.filter-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.overdue {
  color: #ff4d4f;
  font-weight: bold;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
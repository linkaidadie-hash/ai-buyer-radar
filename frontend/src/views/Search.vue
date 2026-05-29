<template>
  <div class="search-page">
    <h2>搜索采购商</h2>

    <div class="card">
      <el-form :model="form" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="关键词">
              <el-input v-model="form.keyword" placeholder="产品/公司/行业" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="国家">
              <el-input v-model="form.country" placeholder="如: UAE, Saudi Arabia" clearable />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="AI等级">
              <el-select v-model="form.ai_level" placeholder="全部" clearable>
                <el-option label="A级" value="A" />
                <el-option label="B级" value="B" />
                <el-option label="C级" value="C" />
                <el-option label="D级" value="D" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="状态">
              <el-select v-model="form.status" placeholder="全部" clearable>
                <el-option label="新增" value="new" />
                <el-option label="已联系" value="contacted" />
                <el-option label="已回复" value="replied" />
                <el-option label="有意向" value="interested" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="AI评分">
              <el-input-number v-model="form.ai_score_min" :min="0" :max="100" placeholder="最低分" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <el-button type="primary" @click="executeSearch">
            <el-icon><Search /></el-icon> 搜索
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="card" v-loading="loading">
      <div v-if="results.length > 0">
        <p class="result-count">找到 {{ total }} 条结果</p>
        <el-table :data="results" @row-click="viewDetail">
          <el-table-column prop="company_name" label="公司名称" min-width="200" />
          <el-table-column prop="country" label="国家" width="120" />
          <el-table-column prop="industry" label="行业" width="120" />
          <el-table-column prop="ai_score" label="评分" width="80">
            <template #default="{ row }">
              <span :class="`level-${row.ai_level?.toLowerCase()}`">{{ row.ai_score || '-' }}</span>
            </template>
          </el-table-column>
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
        </el-table>
        <div class="pagination">
          <el-pagination
            v-model:current-page="page"
            :total="total"
            :page-size="20"
            layout="total, prev, pager, next"
            @current-change="executeSearch"
          />
        </div>
      </div>
      <el-empty v-else-if="!loading" description="输入条件搜索" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { searchAPI } from '../services/api'
import { Search } from '@element-plus/icons-vue'

const router = useRouter()
const loading = ref(false)
const results = ref([])
const total = ref(0)
const page = ref(1)

const form = ref({
  keyword: '',
  country: '',
  ai_level: '',
  status: '',
  ai_score_min: null
})

function statusLabel(status) {
  const labels = { new: '新增', contacted: '已联系', replied: '已回复', interested: '有意向', quoted: '已报价', closed: '已成交', invalid: '无效' }
  return labels[status] || status
}

function levelType(level) {
  return { A: 'success', B: 'primary', C: 'warning', D: 'danger' }[level] || 'info'
}

async function executeSearch() {
  loading.value = true
  try {
    const params = { page: page.value, ...form.value }
    const res = await searchAPI.advanced(params)
    results.value = res.data
    total.value = res.total
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.value = { keyword: '', country: '', ai_level: '', status: '', ai_score_min: null }
  page.value = 1
}

function viewDetail(row) {
  router.push(`/buyers/${row.id}`)
}
</script>

<style scoped>
.result-count {
  margin-bottom: 15px;
  color: #666;
}
</style>
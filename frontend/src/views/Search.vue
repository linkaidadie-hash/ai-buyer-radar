<template>
  <div class="search-page">
    <h2>搜索采购商</h2>

    <!-- 搜索模式切换 -->
    <div class="card">
      <el-radio-group v-model="searchMode" size="large" @change="onModeChange">
        <el-radio-button value="online">搜索新商户</el-radio-button>
        <el-radio-button value="local">搜索已保存商户</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 搜索新商户 -->
    <div class="card" v-if="searchMode === 'online'">
      <el-form :model="onlineForm" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="产品关键词">
              <el-input v-model="onlineForm.keyword" placeholder="如: jewelry wholesaler, rubber necklace importer" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="国家/地区">
              <el-input v-model="onlineForm.country" placeholder="如: UAE, 沙特, Vietnam" clearable />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="数据源">
              <el-select v-model="onlineForm.source" placeholder="选择数据源">
                <el-option
                  v-for="s in availableSources"
                  :key="s.name"
                  :label="s.display_name"
                  :value="s.name"
                  :disabled="!s.configured"
                >
                  <span>{{ s.display_name }}</span>
                  <el-tag v-if="!s.configured" size="small" type="danger" style="margin-left:8px">未配置</el-tag>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="返回数量">
              <el-input-number v-model="onlineForm.limit" :min="5" :max="100" :step="5" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="保存到本地">
              <el-switch v-model="onlineForm.save_to_db" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <el-button type="primary" @click="executeOnlineSearch" :loading="onlineLoading">
            <el-icon><Search /></el-icon> 搜索新商户
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 错误提示 -->
      <el-alert
        v-if="onlineError"
        :title="onlineError.message"
        :description="onlineError.detail"
        type="error"
        show-icon
        closable
        style="margin-top: 10px"
      />

      <!-- 搜索成功但无结果 -->
      <el-alert
        v-if="onlineSearched && !onlineError && onlineResults.length === 0"
        title="本次搜索成功，但未找到匹配商户"
        description="请尝试更换关键词或国家"
        type="warning"
        show-icon
        style="margin-top: 10px"
      />
    </div>

    <!-- 搜索已保存商户 -->
    <div class="card" v-if="searchMode === 'local'">
      <el-form :model="localForm" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="关键词">
              <el-input v-model="localForm.keyword" placeholder="产品/公司/行业" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="国家">
              <el-input v-model="localForm.country" placeholder="如: UAE, Saudi Arabia" clearable />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="AI等级">
              <el-select v-model="localForm.ai_level" placeholder="全部" clearable>
                <el-option label="A级" value="A" />
                <el-option label="B级" value="B" />
                <el-option label="C级" value="C" />
                <el-option label="D级" value="D" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="状态">
              <el-select v-model="localForm.status" placeholder="全部" clearable>
                <el-option label="新增" value="new" />
                <el-option label="已联系" value="contacted" />
                <el-option label="已回复" value="replied" />
                <el-option label="有意向" value="interested" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="AI评分">
              <el-input-number v-model="localForm.ai_score_min" :min="0" :max="100" placeholder="最低分" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <el-button type="primary" @click="executeLocalSearch">
            <el-icon><Search /></el-icon> 搜索已保存商户
          </el-button>
          <el-button @click="resetLocalForm">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 在线搜索结果 -->
    <div class="card" v-if="searchMode === 'online'" v-loading="onlineLoading">
      <div v-if="onlineResults.length > 0">
        <div class="result-summary">
          <p>找到 <strong>{{ onlineSummary.found }}</strong> 个商户，
            导入 <strong>{{ onlineSummary.imported }}</strong> 个，
            重复 <strong>{{ onlineSummary.duplicates }}</strong> 个</p>
        </div>
        <el-table :data="onlineResults" max-height="600">
          <el-table-column prop="company_name" label="公司名称" min-width="180" />
          <el-table-column prop="country" label="国家" width="120" />
          <el-table-column prop="city" label="城市" width="100" />
          <el-table-column prop="industry" label="行业" width="120" />
          <el-table-column prop="phone" label="电话" width="150" />
          <el-table-column prop="website" label="网站" width="150">
            <template #default="{ row }">
              <a v-if="row.website" :href="row.website" target="_blank" class="link">{{ shortUrl(row.website) }}</a>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="source" label="来源" width="100">
            <template #default="{ row }">
              <el-tag size="small">{{ row.source }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-empty v-else-if="!onlineLoading && !onlineSearched" description="输入关键词，搜索互联网新商户" />
    </div>

    <!-- 本地搜索结果 -->
    <div class="card" v-if="searchMode === 'local'" v-loading="localLoading">
      <div v-if="localResults.length > 0">
        <p class="result-count">找到 {{ localTotal }} 条结果</p>
        <el-table :data="localResults" @row-click="viewDetail">
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
            v-model:current-page="localPage"
            :total="localTotal"
            :page-size="20"
            layout="total, prev, pager, next"
            @current-change="executeLocalSearch"
          />
        </div>
      </div>
      <el-empty v-else-if="!localLoading && localSearched" description="本地数据库无匹配结果" />
      <el-empty v-else-if="!localLoading" description="输入条件搜索已保存的商户" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { searchAPI, importAPI } from '../services/api'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()

// 搜索模式
const searchMode = ref('online')

// ============ 在线搜索 ============
const onlineForm = ref({
  keyword: '',
  country: '',
  source: 'google_maps',
  limit: 20,
  save_to_db: true
})
const onlineLoading = ref(false)
const onlineResults = ref([])
const onlineSearched = ref(false)
const onlineError = ref(null)
const onlineSummary = ref({ found: 0, imported: 0, duplicates: 0 })
const availableSources = ref([])

// ============ 本地搜索 ============
const localForm = ref({
  keyword: '',
  country: '',
  ai_level: '',
  status: '',
  ai_score_min: null
})
const localLoading = ref(false)
const localResults = ref([])
const localTotal = ref(0)
const localPage = ref(1)
const localSearched = ref(false)

// 加载可用数据源
async function loadSources() {
  try {
    const sources = await importAPI.sources()
    // 只展示支持搜索的数据源
    availableSources.value = sources.filter(s => s.supports_search)
  } catch (e) {
    console.error('加载数据源失败', e)
  }
}

function onModeChange() {
  onlineError.value = null
}

// 在线搜索
async function executeOnlineSearch() {
  if (!onlineForm.value.keyword) {
    ElMessage.warning('请输入产品关键词')
    return
  }

  onlineLoading.value = true
  onlineError.value = null
  onlineSearched.value = false
  onlineResults.value = []

  try {
    const res = await importAPI.apiSearch({
      keyword: onlineForm.value.keyword,
      country: onlineForm.value.country || null,
      source: onlineForm.value.source,
      limit: onlineForm.value.limit,
      save_to_db: onlineForm.value.save_to_db
    })

    onlineSearched.value = true

    if (res.success === false) {
      onlineError.value = {
        message: res.message || '搜索失败',
        detail: res.detail || ''
      }
      return
    }

    onlineResults.value = res.data || []
    onlineSummary.value = {
      found: res.found || 0,
      imported: res.imported || 0,
      duplicates: res.duplicates || 0
    }

    if (res.found > 0) {
      ElMessage.success(`找到 ${res.found} 个商户`)
    }
  } catch (e) {
    onlineSearched.value = true
    const detail = e.response?.data?.detail || e.message || '请求失败'
    onlineError.value = {
      message: '搜索请求失败',
      detail: detail
    }
  } finally {
    onlineLoading.value = false
  }
}

// 本地搜索
async function executeLocalSearch() {
  localLoading.value = true
  localSearched.value = true
  try {
    const params = { page: localPage.value, ...localForm.value }
    const res = await searchAPI.advanced(params)
    localResults.value = res.data
    localTotal.value = res.total
  } catch (e) {
    ElMessage.error('搜索失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    localLoading.value = false
  }
}

function resetLocalForm() {
  localForm.value = { keyword: '', country: '', ai_level: '', status: '', ai_score_min: null }
  localPage.value = 1
  localResults.value = []
  localTotal.value = 0
  localSearched.value = false
}

function statusLabel(status) {
  const labels = { new: '新增', contacted: '已联系', replied: '已回复', interested: '有意向', quoted: '已报价', closed: '已成交', invalid: '无效' }
  return labels[status] || status
}

function levelType(level) {
  return { A: 'success', B: 'primary', C: 'warning', D: 'danger' }[level] || 'info'
}

function shortUrl(url) {
  if (!url) return ''
  return url.replace(/^https?:\/\/(www\.)?/, '').split('/')[0]
}

function viewDetail(row) {
  router.push(`/buyers/${row.id}`)
}

onMounted(loadSources)
</script>

<style scoped>
.result-count {
  margin-bottom: 15px;
  color: #666;
}
.result-summary {
  margin-bottom: 15px;
  padding: 10px 15px;
  background: #f0f9eb;
  border-radius: 6px;
  color: #333;
}
.result-summary strong {
  color: #67c23a;
}
.link {
  color: #409eff;
  text-decoration: none;
}
.link:hover {
  text-decoration: underline;
}
</style>

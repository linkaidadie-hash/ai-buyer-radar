<template>
  <div class="import-page">
    <h2>数据导入</h2>

    <el-tabs v-model="activeTab">
      <!-- CSV导入 -->
      <el-tab-pane label="CSV导入" name="csv">
        <div class="card">
          <el-steps :active="stepActive" finish-status="success">
            <el-step title="选择文件" />
            <el-step title="配置" />
            <el-step title="导入" />
          </el-steps>

          <div class="step-content">
            <!-- 步骤1: 上传 -->
            <div v-if="stepActive === 0" class="upload-step">
              <el-upload
                drag
                accept=".csv"
                :auto-upload="false"
                :limit="1"
                @change="handleFileChange"
              >
                <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                <div class="el-upload__text">拖拽CSV文件 或 <em>点击上传</em></div>
              </el-upload>
              
              <div class="source-selector">
                <p>数据来源:</p>
                <el-radio-group v-model="csvSource">
                  <el-radio label="volza">Volza</el-radio>
                  <el-radio label="panjiva">Panjiva</el-radio>
                  <el-radio label="importgenius">ImportGenius</el-radio>
                  <el-radio label="manual">手动/通用格式</el-radio>
                </el-radio-group>
              </div>
            </div>

            <!-- 步骤2: 配置 -->
            <div v-if="stepActive === 1" class="config-step">
              <p>已选择: <strong>{{ fileName }}</strong></p>
              <p>来源: {{ csvSource }}</p>
              <el-checkbox v-model="enableAIScore">导入后启用AI评分</el-checkbox>
            </div>

            <!-- 步骤3: 执行 -->
            <div v-if="stepActive === 2" class="import-result" v-loading="importing">
              <div v-if="importResult">
                <p>导入完成!</p>
                <p>成功: {{ importResult.imported }}, 失败: {{ importResult.failed }}</p>
              </div>
              <div v-else>
                <el-icon size="40" class="is-loading"><Loading /></el-icon>
                <p>正在导入...</p>
              </div>
            </div>

            <div class="step-actions">
              <el-button v-if="stepActive > 0" @click="stepActive--">上一步</el-button>
              <el-button v-if="stepActive < 2" type="primary" :disabled="!selectedFile" @click="stepActive++">下一步</el-button>
              <el-button v-if="stepActive === 2 && !importResult" type="primary" :loading="importing" @click="executeImport">执行导入</el-button>
              <el-button v-if="importResult" @click="resetImport">重新导入</el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- API搜索 -->
      <el-tab-pane label="API搜索" name="api">
        <div class="card">
          <el-form :model="searchForm" label-width="100px">
            <el-form-item label="产品关键词">
              <el-input v-model="searchForm.keyword" placeholder="如: cosmetic, building materials" />
            </el-form-item>
            <el-form-item label="国家">
              <el-input v-model="searchForm.country" placeholder="如: UAE, Saudi Arabia" />
            </el-form-item>
            <el-form-item label="数据源">
              <el-select v-model="searchForm.source" style="width: 100%;">
                <el-option label="Google Maps" value="google_maps" />
                <el-option label="LinkedIn" value="linkedin" />
                <el-option label="ZoomInfo" value="zoominfo" />
                <el-option label="Apollo" value="apollo" />
              </el-select>
            </el-form-item>
            <el-form-item label="数量限制">
              <el-input-number v-model="searchForm.limit" :min="1" :max="100" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="searching" @click="executeSearch">搜索</el-button>
            </el-form-item>
          </el-form>

          <div v-if="searchResults.length > 0" class="search-results">
            <h4>搜索结果 ({{ searchResults.length }}条)</h4>
            <el-table :data="searchResults" size="small">
              <el-table-column prop="company_name" label="公司名称" />
              <el-table-column prop="country" label="国家" width="120" />
              <el-table-column prop="website" label="网站" />
            </el-table>
          </div>
        </div>
      </el-tab-pane>

      <!-- 导入历史 -->
      <el-tab-pane label="导入历史" name="history">
        <div class="card">
          <el-table :data="importHistory">
            <el-table-column prop="batch_id" label="批次号" width="100" />
            <el-table-column prop="source" label="来源" width="100" />
            <el-table-column prop="file_name" label="文件名" />
            <el-table-column prop="total_records" label="总数" width="80" />
            <el-table-column prop="imported_records" label="成功" width="80" />
            <el-table-column prop="failed_records" label="失败" width="80" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" />
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { importAPI } from '../services/api'
import { ElMessage } from 'element-plus'
import { UploadFilled, Loading } from '@element-plus/icons-vue'

const activeTab = ref('csv')
const stepActive = ref(0)
const selectedFile = ref(null)
const fileName = ref('')
const csvSource = ref('volza')
const enableAIScore = ref(true)
const importing = ref(false)
const importResult = ref(null)

const searchForm = ref({
  keyword: '',
  country: '',
  source: 'google_maps',
  limit: 50
})
const searching = ref(false)
const searchResults = ref([])

const importHistory = ref([])

function handleFileChange(file) {
  selectedFile.value = file.raw
  fileName.value = file.name
}

async function executeImport() {
  if (!selectedFile.value) return
  
  importing.value = true
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('source', csvSource.value)
  formData.append('enable_ai_score', enableAIScore.value)
  
  try {
    const result = await importAPI.csvImport(formData)
    importResult.value = result
    stepActive.value = 2
    ElMessage.success('导入完成')
  } catch (e) {
    ElMessage.error('导入失败: ' + e.message)
  } finally {
    importing.value = false
  }
}

async function executeSearch() {
  searching.value = true
  try {
    const result = await importAPI.apiSearch(searchForm.value)
    searchResults.value = result.data || []
    ElMessage.success(`找到 ${result.found} 条数据，已导入 ${result.imported} 条`)
  } catch (e) {
    ElMessage.error('搜索失败')
  } finally {
    searching.value = false
  }
}

function resetImport() {
  stepActive.value = 0
  selectedFile.value = null
  fileName.value = ''
  importResult.value = null
}

function statusType(status) {
  return { completed: 'success', processing: 'warning', failed: 'danger', pending: 'info' }[status] || 'info'
}

onMounted(async () => {
  try {
    importHistory.value = await importAPI.batches()
  } catch (e) {
    console.error(e)
  }
})
</script>

<style scoped>
.step-content {
  margin: 40px 20px;
  min-height: 200px;
}

.upload-step, .config-step {
  text-align: center;
}

.source-selector {
  margin-top: 30px;
}

.source-selector p {
  margin-bottom: 10px;
  color: #666;
}

.import-result {
  text-align: center;
  padding: 40px;
}

.step-actions {
  margin-top: 30px;
  text-align: center;
}

.search-results {
  margin-top: 30px;
}
</style>
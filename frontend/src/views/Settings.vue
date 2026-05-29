<template>
  <div class="settings-page">
    <h2>系统设置</h2>

    <el-tabs v-model="activeTab">
      <!-- AI配置 -->
      <el-tab-pane label="AI配置" name="ai">
        <div class="card">
          <h3>AI API 配置</h3>
          <el-form :model="aiConfig" label-width="120px">
            <el-form-item label="OpenAI API Key">
              <el-input v-model="aiConfig.openai_key" type="password" placeholder="sk-..." show-password />
            </el-form-item>
            <el-form-item label="DeepSeek API Key">
              <el-input v-model="aiConfig.deepseek_key" type="password" placeholder="DeepSeek API Key" show-password />
            </el-form-item>
            <el-form-item label="使用模型">
              <el-select v-model="aiConfig.model" style="width: 100%;">
                <el-option label="GPT-4o" value="gpt-4o" />
                <el-option label="GPT-4o-mini" value="gpt-4o-mini" />
                <el-option label="GPT-4 Turbo" value="gpt-4-turbo" />
                <el-option label="DeepSeek Chat" value="deepseek-chat" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="saveAIConfig">保存配置</el-button>
            </el-form-item>
          </el-form>

          <el-divider />

          <h3>API使用统计 (近7天)</h3>
          <el-table :data="apiUsage" size="small">
            <el-table-column prop="source" label="数据源" />
            <el-table-column prop="calls" label="调用次数" />
            <el-table-column prop="tokens" label="Token消耗" />
            <el-table-column prop="cost" label="费用(USD)" />
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 数据源配置 -->
      <el-tab-pane label="数据源配置" name="datasource">
        <div class="card">
          <h3>数据源 API 配置</h3>
          <el-table :data="datasources">
            <el-table-column prop="display_name" label="数据源" width="150" />
            <el-table-column prop="name" label="标识" width="120" />
            <el-table-column prop="api_type" label="类型" width="80" />
            <el-table-column prop="enabled" label="启用" width="80">
              <template #default="{ row }">
                <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
                  {{ row.enabled ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="配置">
              <template #default="{ row }">
                <div v-if="row.config && row.config.api_key">
                  <span style="color: #999;">{{ row.config.api_key.substring(0, 8) }}***</span>
                </div>
                <span v-else style="color: #999;">未配置</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button size="small" @click="editDatasource(row)">配置</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 状态管理 -->
      <el-tab-pane label="状态管理" name="status">
        <div class="card">
          <h3>采购商状态说明</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="new">新增 - 刚导入未联系</el-descriptions-item>
            <el-descriptions-item label="contacted">已联系 - 已发送首次联系</el-descriptions-item>
            <el-descriptions-item label="replied">已回复 - 有回复意向</el-descriptions-item>
            <el-descriptions-item label="interested">有意向 - 明确表示兴趣</el-descriptions-item>
            <el-descriptions-item label="quoted">已报价 - 已发送报价</el-descriptions-item>
            <el-descriptions-item label="closed">已成交 - 达成交易</el-descriptions-item>
            <el-descriptions-item label="invalid">无效 - 联系方式无效</el-descriptions-item>
            <el-descriptions-item label="blacklist">黑名单 - 明确拒绝/骗子</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 数据源配置弹窗 -->
    <el-dialog v-model="showDatasourceDialog" :title="currentDatasource?.display_name" width="500px">
      <el-form :model="dsForm" label-width="100px">
        <template v-if="currentDatasource?.name === 'google_maps'">
          <el-form-item label="API Key">
            <el-input v-model="dsForm.api_key" placeholder="Google Maps API Key" />
          </el-form-item>
        </template>
        <template v-else-if="currentDatasource?.name === 'hunter'">
          <el-form-item label="API Key">
            <el-input v-model="dsForm.api_key" placeholder="Hunter.io API Key" />
          </el-form-item>
        </template>
        <template v-else-if="currentDatasource?.name === 'linkedin'">
          <el-form-item label="Client ID">
            <el-input v-model="dsForm.client_id" placeholder="LinkedIn Client ID" />
          </el-form-item>
          <el-form-item label="Client Secret">
            <el-input v-model="dsForm.client_secret" type="password" placeholder="LinkedIn Client Secret" />
          </el-form-item>
        </template>
        <template v-else>
          <p>该数据源暂无需配置的参数或使用CSV模式</p>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="showDatasourceDialog = false">取消</el-button>
        <el-button type="primary" @click="saveDatasource">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { configAPI } from '../services/api'
import { ElMessage } from 'element-plus'

const activeTab = ref('ai')
const saving = ref(false)
const aiConfig = ref({
  openai_key: '',
  deepseek_key: '',
  model: 'gpt-4o'
})
const apiUsage = ref([])
const datasources = ref([])

const showDatasourceDialog = ref(false)
const currentDatasource = ref(null)
const dsForm = ref({})

async function loadAIConfig() {
  try {
    const config = await configAPI.getAIConfig()
    aiConfig.value = {
      openai_key: config.openai_key || '',
      deepseek_key: config.deepseek_key || '',
      model: config.model || 'gpt-4o'
    }
  } catch (e) {
    console.error(e)
  }
}

async function saveAIConfig() {
  saving.value = true
  try {
    await configAPI.updateAIConfig(aiConfig.value)
    ElMessage.success('AI配置已保存')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function loadApiUsage() {
  try {
    apiUsage.value = await configAPI.apiUsage(7)
  } catch (e) {
    console.error(e)
  }
}

async function loadDatasources() {
  try {
    datasources.value = await configAPI.datasources()
  } catch (e) {
    console.error(e)
  }
}

function editDatasource(ds) {
  currentDatasource.value = ds
  dsForm.value = { ...ds.config }
  showDatasourceDialog.value = true
}

async function saveDatasource() {
  try {
    await configAPI.updateDatasource(currentDatasource.value.name, { config: dsForm.value })
    ElMessage.success('数据源配置已保存')
    showDatasourceDialog.value = false
    loadDatasources()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

onMounted(() => {
  loadAIConfig()
  loadApiUsage()
  loadDatasources()
})
</script>
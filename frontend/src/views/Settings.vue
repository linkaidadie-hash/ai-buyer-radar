<template>
  <div class="settings-page">
    <h2>系统设置</h2>

    <el-tabs v-model="activeTab">
      <!-- AI模型配置 -->
      <el-tab-pane label="AI模型配置" name="ai">
        <div class="card">
          <div class="card-header">
            <h3>AI模型供应商</h3>
            <el-button type="primary" size="small" @click="openAddProvider">
              添加供应商
            </el-button>
          </div>

          <el-table :data="providers" v-loading="loadingProviders" stripe>
            <el-table-column prop="display_name" label="名称" min-width="140" />
            <el-table-column prop="provider_type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag size="small" :type="row.provider_type === 'custom' ? 'warning' : ''">
                  {{ row.provider_type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="model" label="模型" min-width="140" />
            <el-table-column label="启用" width="80" align="center">
              <template #default="{ row }">
                <el-switch
                  v-model="row.enabled"
                  size="small"
                  @change="toggleProviderEnabled(row)"
                />
              </template>
            </el-table-column>
            <el-table-column label="默认" width="70" align="center">
              <template #default="{ row }">
                <el-icon
                  v-if="row.is_default"
                  color="#f59e0b"
                  :size="18"
                  style="cursor: default;"
                ><StarFilled /></el-icon>
                <span v-else style="color: #cbd5e1;">-</span>
              </template>
            </el-table-column>
            <el-table-column label="测试状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag
                  v-if="row.last_test_status"
                  :type="row.last_test_status === 'success' ? 'success' : 'danger'"
                  size="small"
                >
                  {{ row.last_test_status === 'success' ? '正常' : '异常' }}
                </el-tag>
                <span v-else style="color: #94a3b8; font-size: 12px;">未测试</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="220" align="center">
              <template #default="{ row }">
                <el-button size="small" @click="openEditProvider(row)">编辑</el-button>
                <el-button size="small" :loading="row._testing" @click="testProvider(row)">测试连接</el-button>
                <el-button
                  v-if="!row.is_default"
                  size="small"
                  type="warning"
                  plain
                  @click="setDefaultProvider(row)"
                >设为默认</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 数据源配置 -->
      <el-tab-pane label="数据源配置" name="datasource">
        <div class="card">
          <div class="card-header">
            <h3>数据源列表</h3>
            <el-button type="primary" size="small" @click="openAddDatasource">
              添加数据源
            </el-button>
          </div>

          <el-table :data="datasources" v-loading="loadingDatasources" stripe>
            <el-table-column prop="display_name" label="数据源" min-width="140" />
            <el-table-column prop="api_type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ row.api_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="已配置" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="row.configured ? 'success' : 'info'" size="small">
                  {{ row.configured ? '已配置' : '未配置' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="启用" width="80" align="center">
              <template #default="{ row }">
                <el-switch v-model="row.enabled" size="small" disabled />
              </template>
            </el-table-column>
            <el-table-column label="测试状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag
                  v-if="row.last_test_status"
                  :type="row.last_test_status === 'success' ? 'success' : 'danger'"
                  size="small"
                >
                  {{ row.last_test_status === 'success' ? '正常' : '异常' }}
                </el-tag>
                <span v-else style="color: #94a3b8; font-size: 12px;">未测试</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="240" align="center">
              <template #default="{ row }">
                <el-button size="small" @click="openDatasourceConfig(row)">配置</el-button>
                <el-button size="small" :loading="row._testing" @click="testDatasource(row)">测试连接</el-button>
                <el-button
                  v-if="isCustomSource(row.name)"
                  size="small"
                  type="danger"
                  plain
                  @click="deleteDatasource(row)"
                >删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- AI供应商编辑/新增弹窗 -->
    <el-dialog
      v-model="showProviderDialog"
      :title="editingProvider ? '编辑AI供应商' : '添加AI供应商'"
      width="520px"
      destroy-on-close
    >
      <el-form :model="providerForm" label-width="110px">
        <el-form-item v-if="providerForm.provider_type === 'custom'" label="名称">
          <el-input v-model="providerForm.name" placeholder="供应商名称" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input
            v-model="providerForm.api_key"
            type="password"
            show-password
            :placeholder="editingProvider ? '留空保留原Key' : '请输入API Key'"
          />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="providerForm.base_url" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="模型">
          <el-input v-model="providerForm.model" placeholder="gpt-4o" />
        </el-form-item>
        <el-form-item label="备用模型">
          <el-input v-model="providerForm.backup_model" placeholder="gpt-4o-mini (可选)" />
        </el-form-item>
        <el-form-item label="超时(秒)">
          <el-input-number v-model="providerForm.timeout" :min="5" :max="300" :step="5" />
        </el-form-item>
        <el-form-item label="最大重试">
          <el-input-number v-model="providerForm.max_retries" :min="0" :max="10" :step="1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showProviderDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingProvider" @click="saveProvider">保存</el-button>
      </template>
    </el-dialog>

    <!-- 数据源配置弹窗 -->
    <el-dialog
      v-model="showDatasourceDialog"
      :title="currentDatasource ? `配置 - ${currentDatasource.display_name}` : '数据源配置'"
      width="500px"
      destroy-on-close
    >
      <el-form :model="dsForm" label-width="110px">
        <!-- csv类型无需配置 -->
        <template v-if="currentDatasource?.name === 'csv'">
          <el-alert title="无需API配置，支持手工导入" type="info" :closable="false" show-icon />
        </template>

        <!-- snov需要api_user_id + api_key -->
        <template v-else-if="currentDatasource?.name === 'snov'">
          <el-form-item label="API User ID">
            <el-input v-model="dsForm.api_user_id" placeholder="Snov.io User ID" />
          </el-form-item>
          <el-form-item label="API Key">
            <el-input v-model="dsForm.api_key" type="password" show-password placeholder="Snov.io API Key" />
          </el-form-item>
        </template>

        <!-- linkedin需要client_id + client_secret -->
        <template v-else-if="currentDatasource?.name === 'linkedin'">
          <el-form-item label="Client ID">
            <el-input v-model="dsForm.client_id" placeholder="LinkedIn Client ID" />
          </el-form-item>
          <el-form-item label="Client Secret">
            <el-input v-model="dsForm.client_secret" type="password" show-password placeholder="LinkedIn Client Secret" />
          </el-form-item>
        </template>

        <!-- 其他类型：serpapi/google_maps/2gis/hunter/apollo 只需api_key -->
        <template v-else>
          <el-form-item label="API Key">
            <el-input
              v-model="dsForm.api_key"
              type="password"
              show-password
              :placeholder="`${currentDatasource?.display_name || ''} API Key`"
            />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="showDatasourceDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingDatasource" @click="saveDatasource">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加自定义数据源弹窗 -->
    <el-dialog
      v-model="showAddDatasourceDialog"
      title="添加自定义数据源"
      width="500px"
      destroy-on-close
    >
      <el-form :model="newDsForm" label-width="110px">
        <el-form-item label="标识名">
          <el-input v-model="newDsForm.name" placeholder="如: my_source (小写字母、数字、下划线)" />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="newDsForm.display_name" placeholder="如: 我的数据源" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="newDsForm.api_type">
            <el-option label="API" value="api" />
            <el-option label="CSV导入" value="csv" />
          </el-select>
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="newDsForm.api_key" type="password" show-password placeholder="可选，后续也可在配置中填写" />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="newDsForm.base_url" placeholder="可选，自定义API地址" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDatasourceDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingNewDatasource" @click="createDatasource">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { aiProvidersAPI, configAPI, importAPI } from '../services/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { StarFilled } from '@element-plus/icons-vue'

const activeTab = ref('ai')

// ====== AI供应商 ======
const providers = ref([])
const loadingProviders = ref(false)
const showProviderDialog = ref(false)
const editingProvider = ref(null)
const savingProvider = ref(false)
const providerForm = ref({
  name: '',
  api_key: '',
  base_url: '',
  model: '',
  backup_model: '',
  timeout: 60,
  max_retries: 3,
  provider_type: 'custom'
})

async function loadProviders() {
  loadingProviders.value = true
  try {
    const data = await aiProvidersAPI.list()
    providers.value = (Array.isArray(data) ? data : data.providers || []).map(p => ({ ...p, _testing: false }))
  } catch (e) {
    console.error(e)
  } finally {
    loadingProviders.value = false
  }
}

function openAddProvider() {
  editingProvider.value = null
  providerForm.value = {
    name: '',
    api_key: '',
    base_url: '',
    model: '',
    backup_model: '',
    timeout: 60,
    max_retries: 3,
    provider_type: 'custom'
  }
  showProviderDialog.value = true
}

function openEditProvider(row) {
  editingProvider.value = row
  providerForm.value = {
    name: row.name || '',
    api_key: '',
    base_url: row.base_url || '',
    model: row.model || '',
    backup_model: row.backup_model || '',
    timeout: row.timeout || 60,
    max_retries: row.max_retries ?? 3,
    provider_type: row.provider_type || 'custom'
  }
  showProviderDialog.value = true
}

async function saveProvider() {
  savingProvider.value = true
  try {
    const payload = { ...providerForm.value }
    // 编辑时如果api_key为空则不发送
    if (editingProvider.value && !payload.api_key) {
      delete payload.api_key
    }
    if (editingProvider.value) {
      await aiProvidersAPI.update(editingProvider.value.id, payload)
      ElMessage.success('供应商已更新')
    } else {
      await aiProvidersAPI.create(payload)
      ElMessage.success('供应商已添加')
    }
    showProviderDialog.value = false
    loadProviders()
  } catch (e) {
    console.error(e)
  } finally {
    savingProvider.value = false
  }
}

async function toggleProviderEnabled(row) {
  try {
    await aiProvidersAPI.update(row.id, { enabled: row.enabled })
  } catch (e) {
    row.enabled = !row.enabled
    console.error(e)
  }
}

async function testProvider(row) {
  row._testing = true
  try {
    const res = await aiProvidersAPI.test(row.id)
    row.last_test_status = res.status || 'success'
    ElMessage.success('连接测试成功')
  } catch (e) {
    row.last_test_status = 'failed'
    ElMessage.error('连接测试失败')
  } finally {
    row._testing = false
  }
}

async function setDefaultProvider(row) {
  try {
    await aiProvidersAPI.setDefault(row.id)
    ElMessage.success('已设为默认')
    loadProviders()
  } catch (e) {
    console.error(e)
  }
}

// ====== 数据源 ======
const datasources = ref([])
const loadingDatasources = ref(false)
const showDatasourceDialog = ref(false)
const currentDatasource = ref(null)
const dsForm = ref({})
const savingDatasource = ref(false)

async function loadDatasources() {
  loadingDatasources.value = true
  try {
    const data = await importAPI.sources()
    datasources.value = (Array.isArray(data) ? data : data.sources || []).map(d => ({ ...d, _testing: false }))
  } catch (e) {
    console.error(e)
  } finally {
    loadingDatasources.value = false
  }
}

function openDatasourceConfig(row) {
  currentDatasource.value = row
  dsForm.value = { ...(row.config || {}) }
  showDatasourceDialog.value = true
}

async function saveDatasource() {
  savingDatasource.value = true
  try {
    await configAPI.updateDatasource(currentDatasource.value.name, { config: dsForm.value })
    ElMessage.success('数据源配置已保存')
    showDatasourceDialog.value = false
    loadDatasources()
  } catch (e) {
    console.error(e)
  } finally {
    savingDatasource.value = false
  }
}

async function testDatasource(row) {
  row._testing = true
  try {
    const res = await configAPI.testDatasource(row.name)
    row.last_test_status = res.status || 'success'
    ElMessage.success('连接测试成功')
  } catch (e) {
    row.last_test_status = 'failed'
    ElMessage.error('连接测试失败')
  } finally {
    row._testing = false
  }
}

// ====== 添加/删除自定义数据源 ======
const showAddDatasourceDialog = ref(false)
const savingNewDatasource = ref(false)
const newDsForm = ref({ name: '', display_name: '', api_type: 'api', api_key: '', base_url: '' })

const BUILTIN_SOURCES = new Set([
  'google_maps', 'serpapi', 'hunter', 'volza', 'panjiva', 'importgenius',
  'linkedin', 'zoominfo', 'apollo', 'clearbit', 'snov', '2gis'
])

function isCustomSource(name) {
  return !BUILTIN_SOURCES.has(name)
}

function openAddDatasource() {
  newDsForm.value = { name: '', display_name: '', api_type: 'api', api_key: '', base_url: '' }
  showAddDatasourceDialog.value = true
}

async function createDatasource() {
  if (!newDsForm.value.name || !newDsForm.value.display_name) {
    ElMessage.warning('请填写标识名和显示名称')
    return
  }
  savingNewDatasource.value = true
  try {
    const config = {}
    if (newDsForm.value.api_key) config.api_key = newDsForm.value.api_key
    if (newDsForm.value.base_url) config.base_url = newDsForm.value.base_url
    await configAPI.createDatasource({
      name: newDsForm.value.name,
      display_name: newDsForm.value.display_name,
      api_type: newDsForm.value.api_type,
      config
    })
    ElMessage.success('数据源添加成功')
    showAddDatasourceDialog.value = false
    loadDatasources()
  } catch (e) {
    const msg = e.response?.data?.detail || '添加失败'
    ElMessage.error(msg)
  } finally {
    savingNewDatasource.value = false
  }
}

async function deleteDatasource(row) {
  try {
    await ElMessageBox.confirm(`确定删除数据源「${row.display_name}」？`, '删除确认', { type: 'warning' })
    await configAPI.deleteDatasource(row.name)
    ElMessage.success('已删除')
    loadDatasources()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || '删除失败')
    }
  }
}

onMounted(() => {
  loadProviders()
  loadDatasources()
})
</script>

<style scoped>
.settings-page h2 {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 20px;
}
</style>

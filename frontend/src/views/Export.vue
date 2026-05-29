<template>
  <div class="export-page">
    <h2>导出管理</h2>

    <div class="card">
      <h3>导出采购商</h3>
      <el-form :model="form" label-width="100px">
        <el-form-item label="国家">
          <el-select v-model="form.country" placeholder="全部" clearable style="width: 100%;">
            <el-option v-for="c in countries" :key="c.country" :label="c.country" :value="c.country" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" placeholder="全部" clearable>
            <el-option label="新增" value="new" />
            <el-option label="已联系" value="contacted" />
            <el-option label="已回复" value="replied" />
            <el-option label="有意向" value="interested" />
            <el-option label="已报价" value="quoted" />
            <el-option label="已成交" value="closed" />
            <el-option label="无效" value="invalid" />
          </el-select>
        </el-form-item>
        <el-form-item label="AI等级">
          <el-select v-model="form.ai_level" placeholder="全部" clearable>
            <el-option label="A级" value="A" />
            <el-option label="B级" value="B" />
            <el-option label="C级" value="C" />
            <el-option label="D级" value="D" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据源">
          <el-select v-model="form.source" placeholder="全部" clearable>
            <el-option v-for="s in sources" :key="s.source" :label="s.source" :value="s.source" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="exportCSV">
            <el-icon><Download /></el-icon> 导出CSV
          </el-button>
          <el-button @click="exportExcel">
            <el-icon><Document /></el-icon> 导出Excel
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="card">
      <h3>导出历史</h3>
      <el-table :data="history" v-loading="loading">
        <el-table-column prop="filename" label="文件名" />
        <el-table-column prop="size" label="大小" width="120">
          <template #default="{ row }">
            {{ formatSize(row.size) }}
          </template>
        </el-table-column>
        <el-table-column prop="created" label="导出时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created) }}
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { searchAPI, exportAPI } from '../services/api'
import { ElMessage } from 'element-plus'
import { Download, Document } from '@element-plus/icons-vue'

const form = ref({
  country: '',
  status: '',
  ai_level: '',
  source: ''
})

const countries = ref([])
const sources = ref([])
const history = ref([])
const loading = ref(false)

function formatSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / 1024 / 1024).toFixed(1) + 'MB'
}

function formatDate(date) {
  if (!date) return '-'
  return new Date(date).toLocaleString()
}

async function exportCSV() {
  try {
    const res = await exportAPI.csv(form.value)
    ElMessage.success('CSV导出成功')
    loadHistory()
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

async function exportExcel() {
  try {
    const res = await exportAPI.excel(form.value)
    ElMessage.success('Excel导出成功')
    loadHistory()
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

async function loadHistory() {
  loading.value = true
  try {
    history.value = await exportAPI.history()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const [c, s] = await Promise.all([searchAPI.countries(), searchAPI.sources()])
    countries.value = c
    sources.value = s
    loadHistory()
  } catch (e) {
    console.error(e)
  }
})
</script>
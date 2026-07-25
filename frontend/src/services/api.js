/**
 * API服务 - 与后端交互
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

const BASE_URL = import.meta.env.VITE_API_BASE || '/api'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' }
})

// 错误消息去重：相同错误5秒内只提示一次
const lastErrorMap = new Map()
function showErrorDebounced(msg) {
  const now = Date.now()
  const last = lastErrorMap.get(msg)
  if (last && now - last < 5000) return
  lastErrorMap.set(msg, now)
  ElMessage.error(msg)
}

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      // 未登录或token过期，跳转登录
      localStorage.removeItem('token')
      window.location.href = '/login'
      return Promise.reject(error)
    }
    const msg = error.response?.data?.detail || error.message || '请求失败'
    showErrorDebounced(msg)
    return Promise.reject(error)
  }
)

// 请求拦截器 - 附加token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ============================================================
// 采购商管理
// ============================================================

export const buyersAPI = {
  // 列表
  list(params) {
    return api.get('/buyers/list', { params })
  },
  
  // 详情
  get(id) {
    return api.get(`/buyers/${id}`)
  },
  
  // 创建
  create(data) {
    return api.post('/buyers', data)
  },
  
  // 更新
  update(id, data) {
    return api.put(`/buyers/${id}`, data)
  },
  
  // 删除
  delete(id) {
    return api.delete(`/buyers/${id}`)
  },
  
  // 统计数据
  stats() {
    return api.get('/buyers/stats/summary')
  },
  
  // 添加进口记录
  addShipment(buyerId, data) {
    return api.post(`/buyers/${buyerId}/shipments`, data)
  },
  
  // 添加联系人
  addContact(buyerId, data) {
    return api.post(`/buyers/${buyerId}/contacts`, data)
  },
  
  // 添加跟进
  addFollowup(buyerId, data) {
    return api.post(`/buyers/${buyerId}/followups`, data)
  }
}

// ============================================================
// 数据导入
// ============================================================

export const importAPI = {
  // CSV导入
  csvImport(formData) {
    return api.post('/import/csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  // API搜索
  apiSearch(data) {
    return api.post('/import/api-search', data)
  },
  
  // 批量评分
  batchScore(buyerIds, model) {
    return api.post('/import/batch-score', { buyer_ids: buyerIds, model })
  },
  
  // 导入批次列表
  batches() {
    return api.get('/import/batches')
  },
  
  // 数据源列表
  sources() {
    return api.get('/import/sources')
  }
}

// ============================================================
// AI评分
// ============================================================

export const aiAPI = {
  // 单条评分
  score(buyerId) {
    return api.post('/ai/score', { buyer_id: buyerId })
  },
  
  // 批量评分
  batchScore(buyerIds) {
    return api.post('/ai/batch-score', { buyer_ids: buyerIds })
  },
  
  // 生成联系话术
  outreach(buyerId, channel, product, language) {
    return api.post('/ai/outreach', {
      buyer_id: buyerId,
      channel,
      product,
      language
    })
  },
  
  // 支持的渠道
  channels() {
    return api.get('/ai/outreach/channels')
  },
  
  // 支持的语言
  languages() {
    return api.get('/ai/outreach/languages')
  }
}

// ============================================================
// 搜索
// ============================================================

export const searchAPI = {
  // 快速搜索
  quick(q, country, limit) {
    return api.get('/search/quick', { params: { q, country, limit } })
  },
  
  // 高级搜索
  advanced(params) {
    return api.get('/search/advanced', { params })
  },
  
  // 国家列表
  countries() {
    return api.get('/search/countries')
  },
  
  // 行业列表
  industries() {
    return api.get('/search/industries')
  },
  
  // 数据源列表
  sources() {
    return api.get('/search/sources')
  }
}

// ============================================================
// 导出
// ============================================================

export const exportAPI = {
  // CSV导出
  csv(params) {
    return api.get('/export/buyers/csv', { params, responseType: 'blob' })
  },
  
  // Excel导出
  excel(params) {
    return api.get('/export/buyers/excel', { params, responseType: 'blob' })
  },
  
  // 导出历史
  history() {
    return api.get('/export/history')
  }
}

// ============================================================
// 系统配置
// ============================================================

export const configAPI = {
  // 获取配置
  get(key) {
    return api.get(`/config/${key}`)
  },
  
  // 设置配置
  set(key, value) {
    return api.put(`/config/${key}`, { key, value })
  },
  
  // AI配置
  getAIConfig() {
    return api.get('/config/ai/config')
  },
  
  updateAIConfig(data) {
    return api.put('/config/ai/config', data)
  },
  
  // 数据源列表
  datasources() {
    return api.get('/config/datasource/list')
  },
  
  // 更新数据源
  updateDatasource(name, data) {
    return api.put(`/config/datasource/${name}`, data)
  },
  
  // 测试数据源连接
  testDatasource(name) {
    return api.post(`/config/datasource/${name}/test`)
  },

  // 添加自定义数据源
  createDatasource(data) {
    return api.post('/config/datasource', data)
  },

  // 删除自定义数据源
  deleteDatasource(name) {
    return api.delete(`/config/datasource/${name}`)
  },
  
  // API使用统计
  apiUsage(days) {
    return api.get('/config/api/usage', { params: { days } })
  }
}

// ============================================================
// AI模型供应商管理
// ============================================================

export const aiProvidersAPI = {
  list() {
    return api.get('/config/ai/providers')
  },
  create(data) {
    return api.post('/config/ai/providers', data)
  },
  update(id, data) {
    return api.put(`/config/ai/providers/${id}`, data)
  },
  delete(id) {
    return api.delete(`/config/ai/providers/${id}`)
  },
  test(id) {
    return api.post(`/config/ai/providers/${id}/test`)
  },
  setDefault(id) {
    return api.put(`/config/ai/providers/${id}/default`)
  }
}

// ============================================================
// 认证
// ============================================================

export const authAPI = {
  login(username, password) {
    return api.post('/auth/login', { username, password })
  },
  logout() {
    return api.post('/auth/logout')
  },
  check() {
    return api.get('/auth/check')
  }
}

export default api
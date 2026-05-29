<template>
  <div class="demo-screen">
    <!-- 顶部导航 -->
    <div class="demo-header">
      <div class="demo-logo">🌍 AI采购商雷达</div>
      <div class="demo-nav">
        <span class="active">搜索</span>
        <span>采购商库</span>
        <span>AI联系</span>
        <span>CRM</span>
      </div>
      <div class="demo-user">演示账号</div>
    </div>

    <!-- 主内容区 -->
    <div class="demo-main">
      <!-- 左侧：搜索面板 -->
      <div class="demo-search-panel">
        <div class="panel-title">🔍 搜索采购商</div>
        
        <!-- 产品输入 -->
        <div class="form-group">
          <label>产品关键词</label>
          <input 
            v-model="searchForm.product" 
            type="text" 
            :placeholder="placeholderText"
            class="demo-input"
          />
          <div class="quick-tags">
            <span @click="searchForm.product = '防晒衣'">防晒衣</span>
            <span @click="searchForm.product = '发饰'">发饰</span>
            <span @click="searchForm.product = '饰品'">饰品</span>
            <span @click="searchForm.product = '服装'">服装</span>
          </div>
        </div>

        <!-- 国家选择 -->
        <div class="form-group">
          <label>目标市场</label>
          <select v-model="searchForm.country" class="demo-input">
            <option value="">全球</option>
            <option value="Nigeria">🇳🇬 尼日利亚</option>
            <option value="Ghana">🇬🇭 加纳</option>
            <option value="Kenya">🇰🇪 肯尼亚</option>
            <option value="South Africa">🇿🇦 南非</option>
            <option value="UAE">🇦🇪 迪拜</option>
            <option value="Saudi Arabia">🇸🇦 沙特</option>
            <option value="Egypt">🇪🇬 埃及</option>
          </select>
        </div>

        <!-- 公司类型 -->
        <div class="form-group">
          <label>采购商类型</label>
          <div class="checkbox-group">
            <label><input type="checkbox" checked /> 进口商</label>
            <label><input type="checkbox" checked /> 批发商</label>
            <label><input type="checkbox" checked /> 分销商</label>
            <label><input type="checkbox" /> 零售商</label>
          </div>
        </div>

        <!-- 搜索按钮 -->
        <button class="demo-btn-primary" @click="doSearch" :disabled="loading">
          <span v-if="!loading">🔍 开始搜索</span>
          <span v-else>搜索中...</span>
        </button>
      </div>

      <!-- 右侧：结果展示 -->
      <div class="demo-results-panel">
        <!-- 结果统计 -->
        <div class="results-header">
          <div class="results-title">
            找到 <span class="count">{{ results.length }}</span> 个目标采购商
          </div>
          <div class="results-filter">
            <select v-model="filterLevel" class="mini-select">
              <option value="">全部等级</option>
              <option value="A">A级优先</option>
              <option value="B">B级重点</option>
              <option value="C">C级普通</option>
            </select>
          </div>
        </div>

        <!-- 采购商列表 -->
        <div class="buyer-list">
          <div 
            v-for="(buyer, index) in displayedResults" 
            :key="index"
            class="buyer-card"
            :class="{ 'selected': selectedBuyer === buyer }"
            @click="selectBuyer(buyer)"
          >
            <div class="buyer-main">
              <div class="buyer-name">{{ buyer.company }}</div>
              <div class="buyer-meta">
                <span class="buyer-country">{{ buyer.country }} / {{ buyer.city }}</span>
                <span class="buyer-rating">⭐ {{ buyer.rating }}</span>
              </div>
            </div>
            <div class="buyer-actions">
              <button class="btn-whatsapp" @click.stop="openWhatsApp(buyer)">
                💬 WhatsApp联系
              </button>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-if="results.length === 0 && !loading" class="empty-state">
            <div class="empty-icon">🔍</div>
            <div class="empty-text">输入产品关键词，开始搜索全球采购商</div>
          </div>
        </div>
      </div>

      <!-- 选中采购商详情 -->
      <div class="demo-detail-panel" v-if="selectedBuyer">
        <div class="panel-title">📋 采购商详情</div>
        
        <div class="detail-section">
          <div class="detail-name">{{ selectedBuyer.company }}</div>
          <div class="detail-meta">
            <span>{{ selectedBuyer.country }}</span>
            <span>{{ selectedBuyer.city }}</span>
            <span>⭐ {{ selectedBuyer.rating }}</span>
          </div>
        </div>

        <div class="detail-section">
          <div class="section-label">联系方式</div>
          <div class="contact-list">
            <div class="contact-item">
              <span class="contact-icon">📱</span>
              <span class="contact-value">{{ selectedBuyer.phone }}</span>
            </div>
            <div class="contact-item" v-if="selectedBuyer.email">
              <span class="contact-icon">📧</span>
              <span class="contact-value">{{ selectedBuyer.email }}</span>
            </div>
            <div class="contact-item">
              <span class="contact-icon">📍</span>
              <span class="contact-value">{{ selectedBuyer.address }}</span>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <div class="section-label">AI评分</div>
          <div class="score-badge">
            <span class="score-num">{{ selectedBuyer.score }}</span>
            <span class="score-label">/ 100</span>
          </div>
          <div class="score-tags">
            <span class="tag">✅ 真实采购商</span>
            <span class="tag">✅ 批发商</span>
            <span class="tag">✅ 有电话</span>
          </div>
        </div>

        <div class="detail-section">
          <div class="section-label">一键联系</div>
          <button class="demo-btn-whatsapp" @click="openWhatsApp(selectedBuyer)">
            💬 发送WhatsApp消息
          </button>
        </div>
      </div>
    </div>

    <!-- 底部状态栏 -->
    <div class="demo-footer">
      <span>📊 共找到 {{ totalBuyers }} 个采购商</span>
      <span>💬 可直接联系 {{ contactableCount }} 个</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const placeholderText = '如：防晒衣、发饰、饰品...'
const loading = ref(false)
const filterLevel = ref('')
const selectedBuyer = ref(null)
const totalBuyers = ref(79)
const contactableCount = ref(76)

const searchForm = ref({
  product: '',
  country: ''
})

const results = ref([])

const displayedResults = computed(() => {
  if (!filterLevel.value) return results.value
  return results.value // 简化，实际可按等级筛选
})

function doSearch() {
  if (!searchForm.value.product) {
    alert('请输入产品关键词')
    return
  }
  
  loading.value = true
  selectedBuyer.value = null
  
  // 模拟搜索
  setTimeout(() => {
    results.value = [
      {
        company: 'Wigmore Trading LTD',
        country: 'Nigeria',
        city: 'Lagos',
        phone: '+234 815 906 2455',
        rating: '4.6',
        score: 85,
        type: 'Wholesaler',
        address: 'Lagos, Nigeria'
      },
      {
        company: 'ALNOORAS TRADING',
        country: 'UAE',
        city: 'Dubai',
        phone: '+971 52 379 1144',
        rating: '4.6',
        score: 82,
        type: 'Wholesaler',
        address: 'Dubai, UAE'
      },
      {
        company: 'NACCOS RETAIL & WHOLESALE',
        country: 'Tanzania',
        city: 'Dar es Salaam',
        phone: '+255 743 777 124',
        rating: '5.0',
        score: 88,
        type: 'Wholesaler',
        address: 'Dar es Salaam, Tanzania'
      },
      {
        company: 'Kristy\'s Wholesale Hair Shop',
        country: 'Ghana',
        city: 'Accra',
        phone: '+233 24 167 5700',
        rating: '5.0',
        score: 90,
        type: 'Wholesaler',
        address: 'Accra, Ghana'
      },
      {
        company: 'ZarWholeSale',
        country: 'South Africa',
        city: 'Johannesburg',
        phone: '+27 81 737 5646',
        rating: '5.0',
        score: 87,
        type: 'Wholesaler',
        address: 'Johannesburg, South Africa'
      }
    ]
    loading.value = false
  }, 1500)
}

function selectBuyer(buyer) {
  selectedBuyer.value = buyer
}

function openWhatsApp(buyer) {
  if (!buyer.phone) return
  const phone = buyer.phone.replace(/\D/g, '')
  window.open(`https://wa.me/${phone}`, '_blank')
}
</script>

<style scoped>
.demo-screen {
  width: 100%;
  height: 100%;
  background: #f5f5f5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  display: flex;
  flex-direction: column;
}

/* 顶部导航 */
.demo-header {
  background: #001529;
  color: white;
  padding: 12px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.demo-logo {
  font-size: 18px;
  font-weight: bold;
}

.demo-nav {
  display: flex;
  gap: 24px;
}

.demo-nav span {
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}

.demo-nav span.active {
  background: #1890ff;
}

.demo-user {
  font-size: 12px;
  opacity: 0.7;
}

/* 主内容区 */
.demo-main {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

/* 搜索面板 */
.demo-search-panel {
  width: 280px;
  background: white;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  color: #666;
}

.demo-input {
  padding: 10px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
}

.demo-input:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.quick-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.quick-tags span {
  padding: 4px 8px;
  background: #f0f0f0;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.quick-tags span:hover {
  background: #e6f7ff;
  color: #1890ff;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  cursor: pointer;
}

.demo-btn-primary {
  background: #1890ff;
  color: white;
  border: none;
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  margin-top: auto;
}

.demo-btn-primary:hover {
  background: #40a9ff;
}

.demo-btn-primary:disabled {
  background: #d9d9d9;
  cursor: not-allowed;
}

/* 结果面板 */
.demo-results-panel {
  flex: 1;
  background: white;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.results-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.results-title {
  font-size: 14px;
  color: #333;
}

.results-title .count {
  color: #1890ff;
  font-weight: 600;
  font-size: 18px;
}

.mini-select {
  padding: 4px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 12px;
}

.buyer-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.buyer-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.buyer-card:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

.buyer-card.selected {
  border-color: #1890ff;
  background: #f0f7ff;
}

.buyer-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.buyer-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #999;
}

.btn-whatsapp {
  background: #25D366;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 14px;
}

/* 详情面板 */
.demo-detail-panel {
  width: 300px;
  background: white;
  border-radius: 8px;
  padding: 20px;
}

.detail-section {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.detail-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.detail-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #999;
}

.section-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}

.contact-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.contact-value {
  color: #333;
}

.score-badge {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 8px;
}

.score-num {
  font-size: 28px;
  font-weight: 600;
  color: #52c41a;
}

.score-label {
  font-size: 12px;
  color: #999;
}

.score-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  padding: 2px 8px;
  background: #f6ffed;
  color: #52c41a;
  border-radius: 4px;
  font-size: 11px;
}

.demo-btn-whatsapp {
  width: 100%;
  background: #25D366;
  color: white;
  border: none;
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

/* 底部 */
.demo-footer {
  background: #fafafa;
  border-top: 1px solid #f0f0f0;
  padding: 10px 20px;
  display: flex;
  gap: 24px;
  font-size: 12px;
  color: #999;
}
</style>
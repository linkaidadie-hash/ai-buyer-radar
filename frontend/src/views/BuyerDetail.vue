<template>
  <div class="buyer-detail" v-loading="loading">
    <div v-if="buyer" class="detail-content">
      <!-- 基本信息 -->
      <div class="card">
        <div class="card-header">
          <h3>{{ buyer.company_name }}</h3>
          <el-tag :type="levelType(buyer.ai_level)">AI-{{ buyer.ai_level }}</el-tag>
        </div>
        
        <div class="info-grid">
          <div class="info-item">
            <label>国家</label>
            <span>{{ buyer.country }}</span>
          </div>
          <div class="info-item">
            <label>城市</label>
            <span>{{ buyer.city }}</span>
          </div>
          <div class="info-item">
            <label>行业</label>
            <span>{{ buyer.industry }}</span>
          </div>
          <div class="info-item">
            <label>AI评分</label>
            <span :class="`level-${buyer.ai_level?.toLowerCase()}`">{{ buyer.ai_score }}</span>
          </div>
          <div class="info-item">
            <label>买家类型</label>
            <span>{{ buyer.buyer_type }}</span>
          </div>
          <div class="info-item">
            <label>风险等级</label>
            <span>{{ buyer.risk_level }}</span>
          </div>
          <div class="info-item">
            <label>状态</label>
            <span :class="`status-tag status-${buyer.status}`">{{ statusLabel(buyer.status) }}</span>
          </div>
          <div class="info-item">
            <label>数据来源</label>
            <span>{{ buyer.source }}</span>
          </div>
        </div>

        <div class="products" v-if="buyer.products?.length">
          <label>主营产品</label>
          <div class="product-tags">
            <el-tag v-for="p in parseJson(buyer.products)" :key="p">{{ p }}</el-tag>
          </div>
        </div>
      </div>

      <!-- 联系方式 -->
      <div class="card">
        <div class="card-header">
          <h3>联系方式</h3>
          <el-button size="small" @click="showEditContact = true">编辑</el-button>
        </div>
        
        <div class="contact-grid">
          <div class="contact-item" v-if="buyer.email">
            <el-icon><Message /></el-icon>
            <a :href="`mailto:${buyer.email}`">{{ buyer.email }}</a>
          </div>
          <div class="contact-item" v-if="buyer.phone">
            <el-icon><Phone /></el-icon>
            <a :href="`tel:${buyer.phone}`">{{ buyer.phone }}</a>
          </div>
          <div class="contact-item" v-if="buyer.whatsapp">
            <el-icon><ChatDotRound /></el-icon>
            <a :href="openWhatsApp(buyer.whatsapp)" target="_blank">{{ buyer.whatsapp }}</a>
          </div>
          <div class="contact-item" v-if="buyer.website">
            <el-icon><Link /></el-icon>
            <a :href="buyer.website" target="_blank">{{ buyer.website }}</a>
          </div>
          <div class="contact-item" v-if="buyer.linkedin">
            <el-icon><Connection /></el-icon>
            <a :href="buyer.linkedin" target="_blank">LinkedIn</a>
          </div>
        </div>
      </div>

      <!-- 进口记录 -->
      <div class="card" v-if="buyer.shipments?.length">
        <div class="card-header">
          <h3>进口记录 ({{ buyer.shipments.length }})</h3>
        </div>
        <el-table :data="buyer.shipments" size="small">
          <el-table-column prop="product" label="产品" />
          <el-table-column prop="hs_code" label="HS Code" width="100" />
          <el-table-column prop="supplier" label="供应商" />
          <el-table-column prop="origin_country" label="原产国" width="100" />
          <el-table-column prop="date" label="日期" width="100" />
          <el-table-column prop="quantity" label="数量" width="80" />
          <el-table-column prop="value" label="价值" width="100" />
        </el-table>
      </div>

      <!-- 联系人 -->
      <div class="card">
        <div class="card-header">
          <h3>联系人</h3>
          <el-button size="small" type="primary" @click="showAddContact = true">添加</el-button>
        </div>
        <el-table :data="buyer.contacts" size="small" v-if="buyer.contacts?.length">
          <el-table-column prop="name" label="姓名" />
          <el-table-column prop="position" label="职位" />
          <el-table-column prop="email" label="邮箱" />
          <el-table-column prop="phone" label="电话" />
          <el-table-column prop="linkedin" label="LinkedIn" />
        </el-table>
        <el-empty v-else description="暂无联系人" />
      </div>

      <!-- 跟进记录 -->
      <div class="card">
        <div class="card-header">
          <h3>跟进记录</h3>
          <el-button size="small" type="primary" @click="showAddFollowup = true">添加跟进</el-button>
        </div>
        <el-table :data="buyer.followups" size="small" v-if="buyer.followups?.length">
          <el-table-column prop="date" label="日期" width="100" />
          <el-table-column prop="method" label="方式" width="80" />
          <el-table-column prop="content" label="内容" />
          <el-table-column prop="result" label="结果" width="80" />
        </el-table>
        <el-empty v-else description="暂无跟进记录" />
      </div>

      <!-- AI分析 -->
      <div class="card">
        <div class="card-header">
          <h3>AI联系辅助</h3>
        </div>
        <div class="outreach-section">
          <el-form :inline="true">
            <el-form-item label="产品">
              <el-input v-model="outreachProduct" placeholder="产品关键词" />
            </el-form-item>
            <el-form-item label="语言">
              <el-select v-model="outreachLanguage" style="width: 100px;">
                <el-option label="English" value="en" />
                <el-option label="العربية" value="ar" />
                <el-option label="Français" value="fr" />
                <el-option label="Español" value="es" />
              </el-select>
            </el-form-item>
            <el-form-item label="渠道">
              <el-select v-model="outreachChannel" style="width: 120px;">
                <el-option label="邮件" value="email" />
                <el-option label="WhatsApp" value="whatsapp" />
                <el-option label="LinkedIn" value="linkedin" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="generating" @click="generateOutreach">生成话术</el-button>
            </el-form-item>
          </el-form>
          
          <div v-if="outreachContent" class="outreach-result">
            <el-input
              v-model="outreachContent"
              type="textarea"
              :rows="6"
              readonly
            />
            <div class="outreach-actions">
              <el-button type="primary" @click="copyOutreach">复制</el-button>
              <el-button v-if="outreachChannel === 'whatsapp'" @click="openWhatsAppWeb">打开WhatsApp</el-button>
              <el-button v-if="outreachChannel === 'email'" @click="openEmail">发送邮件</el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 操作 -->
      <div class="card">
        <div class="card-header">
          <h3>操作</h3>
        </div>
        <div class="actions-row">
          <el-button @click="changeStatus('contacted')">标记已联系</el-button>
          <el-button @click="changeStatus('interested')">标记有意向</el-button>
          <el-button @click="changeStatus('quoted')">标记已报价</el-button>
          <el-button type="danger" @click="changeStatus('invalid')">标记无效</el-button>
          <el-button type="danger" plain @click="changeStatus('blacklist')">加入黑名单</el-button>
        </div>
      </div>
    </div>

    <!-- 添加联系人弹窗 -->
    <el-dialog v-model="showAddContact" title="添加联系人" width="500px">
      <el-form :model="contactForm" label-width="80px">
        <el-form-item label="姓名"><el-input v-model="contactForm.name" /></el-form-item>
        <el-form-item label="职位"><el-input v-model="contactForm.position" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="contactForm.email" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="contactForm.phone" /></el-form-item>
        <el-form-item label="LinkedIn"><el-input v-model="contactForm.linkedin" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddContact = false">取消</el-button>
        <el-button type="primary" @click="addContact">确定</el-button>
      </template>
    </el-dialog>

    <!-- 添加跟进弹窗 -->
    <el-dialog v-model="showAddFollowup" title="添加跟进" width="500px">
      <el-form :model="followupForm" label-width="80px">
        <el-form-item label="方式">
          <el-select v-model="followupForm.method">
            <el-option label="WhatsApp" value="whatsapp" />
            <el-option label="邮件" value="email" />
            <el-option label="LinkedIn" value="linkedin" />
            <el-option label="电话" value="call" />
            <el-option label="会面" value="meet" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容"><el-input v-model="followupForm.content" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="结果">
          <el-select v-model="followupForm.result">
            <el-option label="无响应" value="no_answer" />
            <el-option label="已回复" value="replied" />
            <el-option label="有意向" value="interested" />
            <el-option label="无意向" value="not_interested" />
          </el-select>
        </el-form-item>
        <el-form-item label="下次跟进"><el-date-picker v-model="followupForm.followup_date" type="date" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddFollowup = false">取消</el-button>
        <el-button type="primary" @click="addFollowup">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { buyersAPI, aiAPI } from '../services/api'
import { ElMessage } from 'element-plus'
import { Message, Phone, ChatDotRound, Link, Connection } from '@element-plus/icons-vue'

const route = useRoute()
const loading = ref(false)
const buyer = ref(null)

const showAddContact = ref(false)
const showAddFollowup = ref(false)
const showEditContact = ref(false)

const contactForm = ref({ name: '', position: '', email: '', phone: '', linkedin: '' })
const followupForm = ref({ method: 'email', content: '', result: '', followup_date: '' })

const outreachProduct = ref('')
const outreachLanguage = ref('en')
const outreachChannel = ref('email')
const outreachContent = ref('')
const generating = ref(false)

function parseJson(str) {
  if (!str) return []
  if (Array.isArray(str)) return str
  try { return JSON.parse(str) } catch { return [str] }
}

function statusLabel(status) {
  const labels = { new: '新增', contacted: '已联系', replied: '已回复', interested: '有意向', quoted: '已报价', closed: '已成交', invalid: '无效', blacklist: '黑名单' }
  return labels[status] || status
}

function levelType(level) {
  return { A: 'success', B: 'primary', C: 'warning', D: 'danger' }[level] || 'info'
}

function openWhatsApp(phone) {
  const clean = phone.replace(/\D/g, '')
  return `https://wa.me/${clean}`
}

async function loadData() {
  loading.value = true
  try {
    buyer.value = await buyersAPI.get(route.params.id)
    if (buyer.value.products) {
      // already parsed
    }
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function addContact() {
  try {
    await buyersAPI.addContact(route.params.id, contactForm.value)
    ElMessage.success('添加成功')
    showAddContact.value = false
    loadData()
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

async function addFollowup() {
  try {
    const data = { ...followupForm.value }
    if (data.followup_date) {
      data.followup_date = new Date(data.followup_date).toISOString().split('T')[0]
    }
    await buyersAPI.addFollowup(route.params.id, data)
    ElMessage.success('添加成功')
    showAddFollowup.value = false
    loadData()
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

async function changeStatus(status) {
  try {
    await buyersAPI.update(route.params.id, { status })
    ElMessage.success('状态已更新')
    loadData()
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

async function generateOutreach() {
  generating.value = true
  try {
    const res = await aiAPI.outreach(route.params.id, outreachChannel.value, outreachProduct.value, outreachLanguage.value)
    outreachContent.value = res.content || res.request_note || ''
  } catch (e) {
    ElMessage.error('生成失败')
  } finally {
    generating.value = false
  }
}

function copyOutreach() {
  navigator.clipboard.writeText(outreachContent.value)
  ElMessage.success('已复制')
}

function openWhatsAppWeb() {
  const phone = buyer.value.whatsapp?.replace(/\D/g, '')
  window.open(`https://web.whatsapp.com/send?phone=${phone}`, '_blank')
}

function openEmail() {
  const subject = encodeURIComponent('Inquiry from Supplier')
  const body = encodeURIComponent(outreachContent.value)
  window.open(`mailto:${buyer.value.email}?subject=${subject}&body=${body}`, '_blank')
}

onMounted(loadData)
</script>

<style scoped>
.info-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  margin-bottom: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.info-item label {
  font-size: 12px;
  color: #999;
}

.info-item span {
  font-size: 14px;
  color: #333;
}

.products {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #f0f0f0;
}

.products label {
  font-size: 12px;
  color: #999;
  display: block;
  margin-bottom: 10px;
}

.product-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.contact-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  background: #fafafa;
  border-radius: 6px;
}

.contact-item a {
  color: #1890ff;
  text-decoration: none;
}

.outreach-result {
  margin-top: 20px;
}

.outreach-actions {
  margin-top: 10px;
  display: flex;
  gap: 10px;
}

.actions-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
</style>
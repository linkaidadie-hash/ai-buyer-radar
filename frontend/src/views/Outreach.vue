<template>
  <div class="outreach-page">
    <h2>AI联系辅助</h2>

    <div class="card">
      <el-form :model="form" label-width="100px">
        <el-form-item label="选择采购商">
          <el-select
            v-model="form.buyer_id"
            filterable
            remote
            placeholder="搜索公司名称"
            :remote-method="searchBuyers"
            @change="onBuyerSelect"
            style="width: 100%;"
          >
            <el-option
              v-for="b in buyerOptions"
              :key="b.id"
              :label="b.company_name"
              :value="b.id"
            >
              <span>{{ b.company_name }}</span>
              <span style="color: #999; font-size: 12px; margin-left: 10px;">{{ b.country }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        
        <div v-if="selectedBuyer">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="公司">{{ selectedBuyer.company_name }}</el-descriptions-item>
            <el-descriptions-item label="国家">{{ selectedBuyer.country }}</el-descriptions-item>
            <el-descriptions-item label="AI评分">{{ selectedBuyer.ai_score }}</el-descriptions-item>
            <el-descriptions-item label="AI等级">{{ selectedBuyer.ai_level }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <el-divider />

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="产品">
              <el-input v-model="form.product" placeholder="产品关键词" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="语言">
              <el-select v-model="form.language" style="width: 100%;">
                <el-option label="English" value="en" />
                <el-option label="العربية" value="ar" />
                <el-option label="Français" value="fr" />
                <el-option label="Español" value="es" />
                <el-option label="中文" value="zh" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="联系渠道">
              <el-select v-model="form.channel" style="width: 100%;">
                <el-option label="📧 邮件" value="email" />
                <el-option label="💬 WhatsApp" value="whatsapp" />
                <el-option label="💼 LinkedIn" value="linkedin" />
                <el-option label="📞 二次跟进" value="followup" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <el-button type="primary" :loading="generating" @click="generate">
            <el-icon><MagicStick /></el-icon> AI生成话术
          </el-button>
          <el-button v-if="result" @click="reset">重新生成</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div v-if="result" class="card">
      <div class="card-header">
        <h3>生成结果 - {{ channelLabel }}</h3>
        <div class="result-actions">
          <el-button type="primary" @click="copy">
            <el-icon><CopyDocument /></el-icon> 复制
          </el-button>
          <el-button v-if="form.channel === 'whatsapp'" @click="openWhatsApp">
            <el-icon><ChatDotRound /></el-icon> 打开WhatsApp
          </el-button>
          <el-button v-if="form.channel === 'email'" @click="openEmail">
            <el-icon><Message /></el-icon> 发送邮件
          </el-button>
        </div>
      </div>
      
      <div v-if="form.channel === 'linkedin'">
        <div class="linkedin-section">
          <h4>连接请求附言:</h4>
          <el-input v-model="result.request_note" type="textarea" :rows="3" readonly />
        </div>
        <div class="linkedin-section">
          <h4>消息内容:</h4>
          <el-input v-model="result.message" type="textarea" :rows="4" readonly />
        </div>
      </div>
      <div v-else>
        <el-input :model-value="result.content || result" type="textarea" :rows="8" readonly />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { buyersAPI, searchAPI, aiAPI } from '../services/api'
import { ElMessage } from 'element-plus'
import { MagicStick, CopyDocument, ChatDotRound, Message } from '@element-plus/icons-vue'

const form = ref({
  buyer_id: null,
  product: '',
  language: 'en',
  channel: 'email'
})

const buyerOptions = ref([])
const selectedBuyer = ref(null)
const generating = ref(false)
const result = ref(null)

const channelLabels = {
  email: '邮件',
  whatsapp: 'WhatsApp',
  linkedin: 'LinkedIn',
  followup: '二次跟进'
}

function channelLabel() {
  return channelLabels[form.value.channel] || form.value.channel
}

async function searchBuyers(query) {
  if (!query) return
  try {
    const res = await searchAPI.quick(query, null, 20)
    buyerOptions.value = res
  } catch (e) {
    console.error(e)
  }
}

async function onBuyerSelect(id) {
  if (!id) return
  try {
    selectedBuyer.value = await buyersAPI.get(id)
    if (selectedBuyer.value.products && !form.value.product) {
      const prods = selectedBuyer.value.products
      form.value.product = Array.isArray(prods) ? prods[0] : prods
    }
  } catch (e) {
    console.error(e)
  }
}

async function generate() {
  if (!form.value.buyer_id) {
    ElMessage.warning('请先选择采购商')
    return
  }
  generating.value = true
  try {
    result.value = await aiAPI.outreach(
      form.value.buyer_id,
      form.value.channel,
      form.value.product,
      form.value.language
    )
  } catch (e) {
    ElMessage.error('生成失败')
  } finally {
    generating.value = false
  }
}

function copy() {
  const text = result.value.content || result.value.request_note || result.value.message || result.value
  navigator.clipboard.writeText(text)
  ElMessage.success('已复制')
}

function openWhatsApp() {
  if (selectedBuyer.value?.whatsapp) {
    const phone = selectedBuyer.value.whatsapp.replace(/\D/g, '')
    const text = encodeURIComponent(result.value.content || result.value)
    window.open(`https://web.whatsapp.com/send?phone=${phone}&text=${text}`, '_blank')
  }
}

function openEmail() {
  if (selectedBuyer.value?.email) {
    const subject = encodeURIComponent('Inquiry about ' + form.value.product)
    const body = encodeURIComponent(result.value.content || result.value)
    window.open(`mailto:${selectedBuyer.value.email}?subject=${subject}&body=${body}`, '_blank')
  }
}

function reset() {
  result.value = null
}
</script>

<style scoped>
.result-actions {
  display: flex;
  gap: 10px;
}

.linkedin-section {
  margin-bottom: 20px;
}

.linkedin-section h4 {
  margin-bottom: 10px;
  color: #666;
}
</style>
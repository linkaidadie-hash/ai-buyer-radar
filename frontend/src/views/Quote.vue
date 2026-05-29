<template>
  <div class="quote-container">
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 产品库 -->
      <el-tab-pane label="产品库" name="products">
        <div class="toolbar">
          <el-button type="primary" @click="showProductDialog = true">+ 添加产品</el-button>
          <el-select v-model="categoryFilter" placeholder="分类筛选" clearable style="width: 150px; margin-left: 10px">
            <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
          </el-select>
        </div>
        
        <el-table :data="filteredProducts" stripe style="width: 100%; margin-top: 15px">
          <el-table-column prop="name_en" label="产品名称" min-width="180" />
          <el-table-column prop="sku" label="SKU" width="120" />
          <el-table-column prop="cost_price" label="成本(¥)" width="90" align="right">
            <template #default="{row}">¥{{ row.cost_price }}</template>
          </el-table-column>
          <el-table-column prop="moq" label="MOQ" width="80" align="right" />
          <el-table-column prop="weight_kg" label="重量(kg)" width="90" align="right">
            <template #default="{row}">{{ row.weight_kg }}kg</template>
          </el-table-column>
          <el-table-column prop="profit_rate" label="利润率" width="90" align="right">
            <template #default="{row}">{{ row.profit_rate }}%</template>
          </el-table-column>
          <el-table-column prop="category" label="分类" width="120" />
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{row}">
              <el-button link type="primary" size="small" @click="quoteProduct(row)">报价</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- AI报价 -->
      <el-tab-pane label="AI报价" name="quote">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card header="产品选择">
              <div v-for="(item, idx) in quoteItems" :key="idx" class="quote-item-row">
                <el-select v-model="item.product_id" placeholder="选择产品" style="width: 200px" 
                  @change="calcQuote">
                  <el-option v-for="p in products" :key="p.id" :label="p.name_en" :value="p.id" />
                </el-select>
                <el-input-number v-model="item.quantity" :min="1" @change="calcQuote" style="margin-left: 10px" />
                <el-button link type="danger" @click="removeQuoteItem(idx)" v-if="quoteItems.length > 1">×</el-button>
              </div>
              <el-button link type="primary" @click="addQuoteItem" style="margin-top: 10px">+ 添加产品</el-button>
            </el-card>

            <el-card header="物流设置" style="margin-top: 15px">
              <el-form label-width="80px" size="small">
                <el-form-item label="目的国">
                  <el-select v-model="quoteForm.country" placeholder="选择国家" style="width: 100%"
                    @change="calcQuote">
                    <el-option v-for="c in countries" :key="c.code" :label="c.name" :value="c.name" />
                  </el-select>
                </el-form-item>
                <el-form-item label="运输方式">
                  <el-radio-group v-model="quoteForm.shipping_method" @change="calcQuote">
                    <el-radio label="sea">海运</el-radio>
                    <el-radio label="air">空运</el-radio>
                  </el-radio-group>
                </el-form-item>
                <el-form-item label="价格条款">
                  <el-select v-model="quoteForm.price_term" style="width: 100%">
                    <el-option label="FOB Shanghai" value="FOB Shanghai" />
                    <el-option label="CIF 目的港" value="CIF" />
                    <el-option label="DDP" value="DDP" />
                  </el-select>
                </el-form-item>
              </el-form>
            </el-card>

              <el-button type="primary" size="large" @click="calcQuote" :loading="calcLoading" style="margin-top: 15px; width: 100%">
                🔮 AI计算报价
              </el-button>
            </el-col>

            <el-col :span="12">
              <el-card header="报价结果" v-if="quoteResult">
                <div class="quote-result">
                  <div class="result-item fob">
                    <span class="label">FOB Shanghai</span>
                    <span class="value">${{ quoteResult.summary.total_fob.toLocaleString() }}</span>
                  </div>
                  
                  <div class="result-item cif">
                    <span class="label">CIF {{ quoteResult.logistics.port_to }}</span>
                    <span class="value highlight">${{ quoteResult.cif.cif_value.toLocaleString() }}</span>
                  </div>

                  <el-divider />

                  <div class="result-section">
                    <h4>📦 运费明细</h4>
                    <div class="detail-row">
                      <span>海运费:</span>
                      <span>${{ quoteResult.logistics.shipping_cost }}</span>
                    </div>
                    <div class="detail-row">
                      <span>港口杂费:</span>
                      <span>${{ quoteResult.logistics.port_fee }}</span>
                    </div>
                    <div class="detail-row">
                      <span>保险费:</span>
                      <span>${{ quoteResult.cif.insurance.toFixed(2) }}</span>
                    </div>
                    <div class="detail-row">
                      <span>总体积:</span>
                      <span>{{ quoteResult.logistics.total_volume_m3 }} m³</span>
                    </div>
                    <div class="detail-row">
                      <span>总重量:</span>
                      <span>{{ quoteResult.logistics.total_weight_kg }} kg</span>
                    </div>
                  </div>

                  <el-divider />

                  <div class="result-section profit">
                    <h4>💰 利润分析</h4>
                    <div class="detail-row">
                      <span>成本:</span>
                      <span>¥{{ quoteResult.summary.total_cost_cny.toLocaleString() }}</span>
                    </div>
                    <div class="detail-row">
                      <span>毛利润:</span>
                      <span class="profit-value">¥{{ quoteResult.summary.profit_cny.toLocaleString() }}</span>
                    </div>
                    <div class="detail-row">
                      <span>利润率:</span>
                      <span class="profit-value">{{ quoteResult.summary.profit_rate }}%</span>
                    </div>
                  </div>

                  <el-divider />

                  <div class="result-section" v-if="shippingRate">
                    <h4>🚢 运输信息</h4>
                    <div class="detail-row">
                      <span>目的港:</span>
                      <span>{{ shippingRate.port }}</span>
                    </div>
                    <div class="detail-row">
                      <span>运输天数:</span>
                      <span>{{ shippingRate.transit_days }}</span>
                    </div>
                  </div>
                </div>
              </el-card>
              <el-card v-else header="报价结果">
                <el-empty description="选择产品后点击AI计算报价" />
              </el-card>

              <!-- 生成报价单按钮 -->
              <el-button v-if="quoteResult" type="success" size="large" 
                @click="showQuotationDialog = true" style="margin-top: 15px; width: 100%">
                📄 生成报价单
              </el-button>
            </el-col>
          </el-row>
      </el-tab-pane>

      <!-- 报价单 -->
      <el-tab-pane label="报价单" name="quotations">
        <el-table :data="quotations" stripe style="width: 100%">
          <el-table-column prop="quotation_no" label="报价单号" width="150" />
          <el-table-column prop="buyer_name" label="客户" min-width="150" />
          <el-table-column prop="buyer_country" label="国家" width="100" />
          <el-table-column prop="total_amount" label="金额(USD)" width="120" align="right">
            <template #default="{row}">${{ row.total_amount?.toLocaleString() }}</template>
          </el-table-column>
          <el-table-column prop="price_term" label="条款" width="120" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{row}">
              <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="valid_until" label="有效期至" width="110" />
          <el-table-column prop="created_at" label="创建时间" width="160" />
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{row}">
              <el-button link type="primary" size="small" @click="viewQuotation(row)">查看</el-button>
              <el-button link type="success" size="small" @click="exportQuotation(row)">导出</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 订单 -->
      <el-tab-pane label="订单" name="orders">
        <el-table :data="orders" stripe style="width: 100%">
          <el-table-column prop="order_no" label="订单号" width="150" />
          <el-table-column prop="buyer_name" label="客户" min-width="150" />
          <el-table-column prop="buyer_country" label="国家" width="100" />
          <el-table-column prop="total_amount" label="金额(USD)" width="120" align="right">
            <template #default="{row}">${{ row.total_amount?.toLocaleString() }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{row}">
              <el-tag :type="orderStatusType(row.status)" size="small">{{ orderStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="160" />
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{row}">
              <el-button link type="primary" size="small" @click="viewOrder(row)">查看</el-button>
              <el-select v-model="row.newStatus" size="small" placeholder="改状态" style="width: 100px" @change="updateOrderStatus(row)">
                <el-option v-for="s in orderStatuses" :key="s.value" :label="s.label" :value="s.value" />
              </el-select>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 运费配置 -->
      <el-tab-pane label="运费配置" name="shipping">
        <el-table :data="shippingRates" stripe style="width: 100%">
          <el-table-column prop="country" label="国家" width="120" />
          <el-table-column prop="port" label="港口" min-width="150" />
          <el-table-column prop="shipping_method" label="方式" width="80">
            <template #default="{row}">
              <el-tag size="small">{{ row.shipping_method === 'sea' ? '海运' : '空运' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="rate_per_m3" label="$/m³" width="90" align="right">
            <template #default="{row}">${{ row.rate_per_m3 }}</template>
          </el-table-column>
          <el-table-column prop="rate_per_kg" label="$/kg" width="90" align="right">
            <template #default="{row}">${{ row.rate_per_kg }}</template>
          </el-table-column>
          <el-table-column prop="min_charge" label="最低收费" width="100" align="right">
            <template #default="{row}">${{ row.min_charge }}</template>
          </el-table-column>
          <el-table-column prop="transit_days" label="运输天数" width="100" />
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 添加产品弹窗 -->
    <el-dialog v-model="showProductDialog" title="添加产品" width="500px">
      <el-form :model="productForm" label-width="100px">
        <el-form-item label="英文名称">
          <el-input v-model="productForm.name_en" />
        </el-form-item>
        <el-form-item label="中文名称">
          <el-input v-model="productForm.name_cn" />
        </el-form-item>
        <el-form-item label="SKU">
          <el-input v-model="productForm.sku" />
        </el-form-item>
        <el-form-item label="成本(¥)">
          <el-input-number v-model="productForm.cost_price" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item label="MOQ">
          <el-input-number v-model="productForm.moq" :min="1" />
        </el-form-item>
        <el-form-item label="重量(kg)">
          <el-input-number v-model="productForm.weight_kg" :min="0" :precision="3" />
        </el-form-item>
        <el-form-item label="尺寸(cm)">
          <el-input placeholder="长" v-model.number="productForm.length_cm" style="width: 80px" /> ×
          <el-input placeholder="宽" v-model.number="productForm.width_cm" style="width: 80px" /> ×
          <el-input placeholder="高" v-model.number="productForm.height_cm" style="width: 80px" />
        </el-form-item>
        <el-form-item label="利润率(%)">
          <el-input-number v-model="productForm.profit_rate" :min="0" :max="200" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="productForm.category" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showProductDialog = false">取消</el-button>
        <el-button type="primary" @click="saveProduct">保存</el-button>
      </template>
    </el-dialog>

    <!-- 生成报价单弹窗 -->
    <el-dialog v-model="showQuotationDialog" title="生成报价单" width="500px">
      <el-form :model="quotationForm" label-width="100px">
        <el-form-item label="客户名称">
          <el-input v-model="quotationForm.buyer_name" />
        </el-form-item>
        <el-form-item label="国家">
          <el-input v-model="quotationForm.buyer_country" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="quotationForm.buyer_phone" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="quotationForm.buyer_email" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showQuotationDialog = false">取消</el-button>
        <el-button type="success" @click="generateQuotation">生成报价单</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const API = '/api/quote'

// 数据
const products = ref([])
const quotations = ref([])
const orders = ref([])
const shippingRates = ref([])
const countries = ref([])
const orderStatuses = ref([])
const categories = computed(() => [...new Set(products.value.map(p => p.category).filter(Boolean))])

// 状态
const activeTab = ref('quote')
const categoryFilter = ref('')
const showProductDialog = ref(false)
const showQuotationDialog = ref(false)
const calcLoading = ref(false)

// 表单
const productForm = ref({
  name_en: '', name_cn: '', sku: '', cost_price: 0, moq: 100,
  weight_kg: 0, length_cm: 0, width_cm: 0, height_cm: 0,
  profit_rate: 30, category: ''
})

const quoteItems = ref([{ product_id: null, quantity: 100 }])
const quoteForm = ref({ country: 'Nigeria', shipping_method: 'sea', price_term: 'FOB Shanghai' })
const quoteResult = ref(null)
const shippingRate = ref(null)

const quotationForm = ref({
  buyer_name: '', buyer_country: '', buyer_phone: '', buyer_email: ''
})

// 过滤产品
const filteredProducts = computed(() => {
  if (!categoryFilter.value) return products.value
  return products.value.filter(p => p.category === categoryFilter.value)
})

// 加载数据
async function loadData() {
  try {
    const [p, q, o, s, c, st] = await Promise.all([
      axios.get(`${API}/products`),
      axios.get(`${API}/quotations`),
      axios.get(`${API}/orders`),
      axios.get(`${API}/shipping/rates`),
      axios.get(`${API}/countries`),
      axios.get(`${API}/order/statuses`)
    ])
    products.value = p.data
    quotations.value = q.data
    orders.value = o.data
    shippingRates.value = s.data
    countries.value = c.data
    orderStatuses.value = st.data
  } catch (e) {
    console.error(e)
  }
}

// 添加产品
async function saveProduct() {
  await axios.post(`${API}/products`, productForm.value)
  showProductDialog.value = false
  loadData()
  ElMessage.success('产品添加成功')
}

// 报价项
function addQuoteItem() {
  quoteItems.value.push({ product_id: null, quantity: 100 })
}

function removeQuoteItem(idx) {
  quoteItems.value.splice(idx, 1)
}

function quoteProduct(row) {
  quoteItems.value = [{ product_id: row.id, quantity: row.moq || 100 }]
  activeTab.value = 'quote'
  calcQuote()
}

// 计算报价
async function calcQuote() {
  if (!quoteItems.value[0].product_id) return
  calcLoading.value = true
  try {
    const { data } = await axios.post(`${API}/calculate`, {
      items: quoteItems.value,
      country: quoteForm.value.country,
      shipping_method: quoteForm.value.shipping_method,
      price_term: quoteForm.value.price_term
    })
    quoteResult.value = data
    
    // 获取运费信息
    const { data: rates } = await axios.get(`${API}/shipping/rates?country=${quoteForm.value.country}`)
    shippingRate.value = rates.find(r => r.shipping_method === quoteForm.value.shipping_method) || null
  } catch (e) {
    ElMessage.error('计算失败: ' + e.message)
  } finally {
    calcLoading.value = false
  }
}

// 生成报价单
async function generateQuotation() {
  try {
    const { data } = await axios.post(`${API}/quotations`, {
      ...quotationForm.value,
      items: quoteItems.value,
      country: quoteForm.value.country,
      shipping_method: quoteForm.value.shipping_method
    })
    ElMessage.success(`报价单 ${data.quotation_no} 生成成功`)
    showQuotationDialog.value = false
    loadData()
  } catch (e) {
    ElMessage.error('生成失败')
  }
}

function viewQuotation(row) {
  ElMessage.info('报价单详情: ' + row.quotation_no)
}

function exportQuotation(row) {
  ElMessage.success('报价单导出: ' + row.quotation_no)
}

function viewOrder(row) {
  ElMessage.info('订单详情: ' + row.order_no)
}

async function updateOrderStatus(row) {
  await axios.put(`${API}/orders/${row.id}/status?status=${row.newStatus}`)
  row.status = row.newStatus
  ElMessage.success('状态已更新')
}

function statusType(s) {
  return { draft: 'info', sent: 'primary', confirmed: 'success', rejected: 'danger', expired: 'warning' }[s] || 'info'
}
function statusLabel(s) {
  return { draft: '草稿', sent: '已发', confirmed: '已确认', rejected: '已拒绝', expired: '已过期' }[s] || s
}
function orderStatusType(s) {
  return { inquiry: 'info', quote: 'primary', sample: 'warning', payment: 'warning', production: 'primary', shipped: 'success', delivered: 'success', completed: 'info', cancelled: 'danger' }[s] || 'info'
}
function orderStatusLabel(s) {
  return { inquiry: '询盘中', quote: '已报价', sample: '打样中', payment: '待付款', production: '生产中', shipped: '已发货', delivered: '已到港', completed: '已完成', cancelled: '已取消' }[s] || s
}

onMounted(loadData)
</script>

<style scoped>
.quote-container { padding: 20px; }
.toolbar { display: flex; align-items: center; }
.quote-item-row { display: flex; align-items: center; margin-bottom: 10px; gap: 10px; }
.quote-result { padding: 10px; }
.result-item { display: flex; justify-content: space-between; padding: 15px; background: #f5f7fa; border-radius: 8px; margin-bottom: 10px; }
.result-item.fob { background: #ecf5ff; }
.result-item.cif { background: #f0f9eb; }
.result-item .label { font-size: 14px; color: #666; }
.result-item .value { font-size: 24px; font-weight: bold; }
.result-item .value.highlight { color: #67c23a; }
.result-section h4 { margin: 10px 0; color: #333; }
.detail-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px dashed #eee; }
.detail-row:last-child { border-bottom: none; }
.profit-value { color: #67c23a; font-weight: bold; }
</style>
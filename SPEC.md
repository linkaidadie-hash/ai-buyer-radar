# AI海外采购商雷达系统 V1
## AI Buyer Radar V1 - 更新版产品定位

> 不是外贸CRM，不是ERP，不是群发工具。
> 而是：**AI Importer Finder** / **AI采购商雷达**

---

## 一、核心定位（已更新）

**输入：** 产品关键词 + 国家

**输出：** 真实海外采购商 + 联系方式 + AI评分 + AI联系辅助

**核心差异化：** "Google Maps + Hunter + Snov" 三位一体
- 覆盖新兴市场（中东/非洲/东南亚）
- 很多采购商没有LinkedIn/官网/标准邮箱
- 但有：Google商家 + 电话 + WhatsApp

---

## 二、数据源矩阵（已验证8个）

| 数据源 | 状态 | 功能 |
|--------|------|------|
| **SerpApi** | ✅ 核心 | Google Maps搜索 → 公司/电话/地址/评分 |
| **Hunter.io** | ✅ 核心 | 域名 → 邮箱（质量高） |
| **Snov.io** | ✅ 重要 | 域名 → 公司信息补全 |
| **Apollo.io** | ⚠️ 留着 | 等付费解锁联系人 |
| **ScraperAPI** | ✅ 备用 | 抓官网补充联系人 |
| **Nominatim** | ✅ 补充 | 坐标 → 地址 |
| **Apify** | ⚠️ 备用 | 0积分需充值 |
| **ZeroBounce** | ⚠️ 待确认 | 邮箱验证 |

---

## 三、核心数据流

```
产品关键词 + 国家
      ↓
SerpApi Google Maps
      ↓
获取采购商列表（公司名/电话/地址/评分）
      ↓
      ↓ 【关键区分点】
      ↓
AI自动识别公司类型（Importer/Wholesaler/Distributor/Trading/Retail）
      ↓
过滤零售店、个人店、小门店
      ↓
Hunter.io → 域名 → 邮箱
      ↓
WhatsApp自动检测 → 生成 wa.me/链接
      ↓
网站质量评分（官网是否真实公司）
      ↓
AI综合评分 → A/B/C/D等级 → 推荐联系渠道
      ↓
生成联系话术（WhatsApp/邮件/LinkedIn）
      ↓
半自动联系
      ↓
CRM跟进
```

---

## 四、AI评分维度（已增强）

| 维度 | 分值 | 说明 |
|------|------|------|
| 是否真实采购商 | 0-25 | 业务实体真实性 |
| 公司类型匹配度 | 0-25 | **Importer/Wholesaler/Distributor** 得高分 |
| 采购能力 | 0-20 | 进口记录+产品匹配度 |
| 联系方式质量 | 0-15 | 邮箱/电话/WhatsApp/网站 |
| 国家风险 | 0-15 | 低风险国家高分 |

**新增：公司类型识别**
- Importer ✅ 最优先
- Wholesaler ✅ 次优先
- Distributor ✅
- Trading Company ✅
- Factory ⚠️ 可能不是采购商
- Retail ❌ 过滤
- 个人店 ❌ 过滤

---

## 五、公司类型识别规则

### 必须保留（Target）
- [ ] Importer
- [ ] Wholesaler
- [ ] Distributor
- [ ] Trading Company
- [ ] Wholesale in name
- [ ] Import in name

### 必须过滤（Filter）
- [ ] Retail
- [ ] Store
- [ ] Shop
- [ ] 个人姓名（非公司）
- [ ] "meters" / "kg" 等散卖单位
- [ ] 仅"Market"无公司名

### 需要验证（Verify）
- [ ] Factory（可能是供应商不是采购商）
- [ ] Agent（可能是中间商）

---

## 六、WhatsApp自动检测

```
电话 +971XXXXXXXX → wa.me/971XXXXXXXX
电话 +234XXXXXXXX → wa.me/234XXXXXXXX
```

**检测逻辑：**
1. 电话格式标准化
2. 生成 wa.me/ 链接
3. 可选：验证WhatsApp是否有效（通过ScraperAPI）

---

## 七、联系方式优先级

| 联系方式 | 优先级 | 说明 |
|----------|--------|------|
| WhatsApp | ⭐⭐⭐ 首选 | 新兴市场最常用 |
| 电话/SMS | ⭐⭐ 次选 | 直接联系 |
| 邮箱 | ⭐⭐ 重要 | 正式沟通 |
| LinkedIn | ⭐ 辅助 | 有则用 |
| 官网表单 | ⭐ 备用 | 无其他联系方式 |

---

## 八、市场覆盖（已验证）

| 市场 | SerpApi | WhatsApp覆盖 | 示例 |
|------|---------|--------------|------|
| 中东UAE | ✅ 强 | ✅ 高 | 迪拜服装批发 |
| 沙特 | ⚠️ 需优化 | ✅ 高 | 保暖内衣 |
| 尼日利亚 | ✅ 良好 | ✅ 高 | 建材分销 |
| 肯尼亚 | ✅ | ✅ | 建材 |
| 埃及 | ✅ | ✅ | - |
| 东南亚 | ✅ | ✅ | - |

---

## 九、搜索质量优化规则

### 关键词增强
```
Dubai clothing wholesaler
Dubai textile importer
Nigeria building materials distributor
Saudi thermal underwear importer
```

### 过滤规则
1. 名称含 "Retail" / "Store" / "Shop" → 降级或过滤
2. 评分<3.0 → 低优先级
3. 无电话无邮箱 → 低优先级
4. 地址过于模糊 → 降级

---

## 十、联系策略AI判断

| 公司特征 | 推荐渠道 | 话术风格 |
|----------|----------|----------|
| 有WhatsApp + 无邮箱 | WhatsApp | 简短+图片 |
| 有邮箱 + 无WhatsApp | 邮件 | 正式开发信 |
| 两者都有 | WhatsApp优先 | 简短引荐 |
| 无联系方式 | 尝试Hunter补全 | - |

---

## 十一、下一步行动

### 现在（立即测试）
1. 迪拜服装批发商 → 测试完整流程
2. 尼日利亚建材 → 验证电话质量
3. 沙特保暖内衣 → 优化搜索精度

### 短期（本周）
1. 公司类型识别模块
2. WhatsApp自动检测
3. 搜索质量过滤规则
4. 真实业务验证

### 中期（下月）
1. 联系回复率统计
2. 话术优化
3. 数据可视化面板
4. 打包桌面版

---

## 十二、护城河（已明确）

1. ✅ **新兴市场Google Maps数据**
2. ✅ **三位一体联系方式拼接**（Maps+Hunter+Snov）
3. ✅ **AI采购商识别**（过滤零售/个人）
4. ✅ **WhatsApp生态覆盖**
5. ✅ **中国供应链理解**

---

## 十三、商业模式

- **软件订阅**：月付/年付
- **行业版**：中东建材版/非洲服装版
- **代找采购商服务**：按需付费

---

## 十四、注意事项

**不要继续堆API。**
现在数据源已经够用。
最重要的是：**真实业务验证**。

---

*更新于 2026-05-28*
*基于用户反馈优化方向：搜索质量 > 堆API*
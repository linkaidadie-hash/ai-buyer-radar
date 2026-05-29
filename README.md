# AI海外采购商雷达系统 V1

> 输入产品关键词 + 国家 → 真实海外采购商 + 联系方式 + AI评分 + AI联系辅助

## 🚀 快速开始

### 1. 安装后端依赖

```bash
cd buyer-radar
pip install -r requirements.txt
```

### 2. 启动后端API

```bash
cd backend
python main.py
# 或使用uvicorn
uvicorn main:app --reload --port 8000
```

API文档: http://localhost:8000/docs

### 3. 启动前端开发服务器

```bash
cd frontend
npm install
npm run dev
```

浏览器打开: http://localhost:5173

## 📁 项目结构

```
buyer-radar/
├── backend/
│   ├── main.py              # FastAPI入口
│   ├── routers/            # API路由
│   │   ├── buyers.py       # 采购商管理
│   │   ├── search.py       # 搜索
│   │   ├── import_data.py  # 数据导入
│   │   ├── ai_score.py     # AI评分
│   │   ├── contacts.py     # 联系人
│   │   ├── followups.py    # 跟进
│   │   ├── export.py       # 导出
│   │   └── config.py       # 配置
│   ├── services/           # 业务服务
│   │   ├── database.py     # 数据库
│   │   ├── ai_service.py  # AI评分/话术
│   │   └── sources/        # 数据源适配器
│   │       ├── base.py     # 基类
│   │       ├── volza.py    # Volza
│   │       ├── google_maps.py
│   │       └── more_sources.py
│   └── models/
├── frontend/
│   ├── src/
│   │   ├── views/         # 页面
│   │   ├── services/       # API服务
│   │   └── router/        # 路由
│   └── package.json
├── database/
│   └── schema.sql         # 数据库Schema
└── docs/
```

## 🔌 数据源

| 数据源 | 用途 | 类型 |
|--------|------|------|
| Volza | 进口商/采购记录 | CSV |
| Google Maps | 企业信息/电话/网站 | API |
| Hunter.io | 邮箱查找/验证 | API |
| Panjiva | 美国进口记录 | CSV |
| ImportGenius | 全球贸易数据 | CSV |
| LinkedIn | 采购负责人 | API |
| ZoomInfo | 企业联系信息 | API |
| Apollo.io | 企业+邮箱 | API |
| Clearbit | 企业补全 | API |

## 🎯 核心功能

- [x] CSV导入 (Volza/Panjiva/ImportGenius/通用)
- [x] AI评分 (判断真实采购商/评分/分类)
- [x] 联系方式补全 (邮箱/电话/WhatsApp/LinkedIn)
- [x] AI联系辅助 (开发信/WhatsApp话术/LinkedIn请求)
- [x] CRM跟进 (状态管理/跟进记录/提醒)
- [x] 数据导出 (CSV/Excel)
- [x] 搜索 (快速搜索/高级筛选)

## 📊 API端点

```
GET  /api/buyers/list          # 采购商列表
GET  /api/buyers/{id}         # 采购商详情
POST /api/buyers              # 创建采购商
PUT  /api/buyers/{id}         # 更新采购商
POST /api/import/csv          # CSV导入
POST /api/import/api-search   # API搜索
POST /api/ai/score            # AI评分
POST /api/ai/outreach         # 生成联系话术
GET  /api/search/advanced      # 高级搜索
GET  /api/export/buyers/csv   # 导出CSV
```

## 🔧 配置

在 `Settings` 页面配置:

1. **AI配置**: OpenAI API Key / DeepSeek API Key
2. **数据源配置**: Google Maps API Key / Hunter.io API Key等

## 📦 数据导入流程

1. 从Volza/Panjiva等导出CSV
2. 进入「数据导入」页面
3. 选择文件 + 选择来源
4. 点击执行导入
5. 导入后自动进入AI评分流程

## 💡 AI评分维度

1. 是否真实采购商 (0-25分)
2. 是否进口商/批发商 (0-25分)
3. 采购能力评估 (0-20分)
4. 联系方式质量 (0-15分)
5. 国家风险 (0-15分)

输出: AI评分(1-100) / 等级(A/B/C/D) / 推荐渠道 / 风险等级

## 📝 开发说明

- 后端: FastAPI + SQLite
- 前端: Vue3 + Element Plus + Vite
- 数据库: SQLite (MVP阶段)，可升级PostgreSQL
- AI: OpenAI / DeepSeek (通过httpx调用)

## 🚢 部署

### 后端
```bash
cd backend
pip install -r requirements.txt
nohup uvicorn main:app --host 0.0.0.0 --port 8000 &
```

### 前端构建
```bash
cd frontend
npm install
npm run build  # 输出到 dist/
```

### Electron桌面版
```bash
npm run electron:build  # 需要额外配置electron-builder
```

## 📄 License

MIT
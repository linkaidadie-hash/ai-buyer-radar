-- AI海外采购商雷达系统 V1 - 数据库Schema
-- SQLite + JSON支持

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ============================================================
-- 采购商表 (buyers)
-- ============================================================
CREATE TABLE IF NOT EXISTS buyers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name    TEXT NOT NULL,
    country         TEXT,
    city            TEXT,
    industry        TEXT,
    products        TEXT,           -- JSON数组: ["product1", "product2"]
    hs_code         TEXT,           -- JSON数组: ["1234", "5678"]
    website         TEXT,
    email           TEXT,
    phone           TEXT,
    whatsapp        TEXT,
    linkedin        TEXT,
    facebook        TEXT,
    source          TEXT,           -- 数据来源: volza/google/hunter/panjiva等
    source_url      TEXT,           -- 原始链接
    ai_score        INTEGER DEFAULT 0,  -- AI评分 1-100
    ai_level        TEXT DEFAULT 'C',   -- A/B/C/D 客户等级
    buyer_type      TEXT,           -- 进口商/批发商/分销商/真实采购商/不确定
    risk_level      TEXT DEFAULT 'medium', -- high/medium/low
    status          TEXT DEFAULT 'new',   -- new/contacted/replied/interested/quoted/closed/invalid/blacklist
    notes           TEXT,
    import_batch    TEXT,           -- 导入批次号
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_buyers_country ON buyers(country);
CREATE INDEX IF NOT EXISTS idx_buyers_status ON buyers(status);
CREATE INDEX IF NOT EXISTS idx_buyers_ai_score ON buyers(ai_score);
CREATE INDEX IF NOT EXISTS idx_buyers_source ON buyers(source);
CREATE INDEX IF NOT EXISTS idx_buyers_company ON buyers(company_name);

-- ============================================================
-- 进口记录表 (shipment_records)
-- ============================================================
CREATE TABLE IF NOT EXISTS shipment_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_id        INTEGER REFERENCES buyers(id) ON DELETE CASCADE,
    product         TEXT NOT NULL,
    hs_code         TEXT,
    supplier        TEXT,
    origin_country  TEXT,
    quantity        TEXT,
    unit            TEXT,
    date            TEXT,
    value           TEXT,
    source          TEXT,
    source_url      TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_shipments_buyer ON shipment_records(buyer_id);
CREATE INDEX IF NOT EXISTS idx_shipments_product ON shipment_records(product);

-- ============================================================
-- 联系人表 (contacts)
-- ============================================================
CREATE TABLE IF NOT EXISTS contacts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_id        INTEGER REFERENCES buyers(id) ON DELETE CASCADE,
    name            TEXT,
    position        TEXT,
    department      TEXT,
    email           TEXT,
    phone           TEXT,
    mobile          TEXT,
    whatsapp        TEXT,
    linkedin        TEXT,
    source          TEXT,
    is_primary      INTEGER DEFAULT 0,  -- 1=主联系人
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_contacts_buyer ON contacts(buyer_id);

-- ============================================================
-- 跟进记录表 (followups)
-- ============================================================
CREATE TABLE IF NOT EXISTS followups (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_id        INTEGER REFERENCES buyers(id) ON DELETE CASCADE,
    date            TEXT DEFAULT (date('now')),
    method          TEXT,           -- whatsapp/linkedin/email/call/meet
    subject         TEXT,
    content         TEXT,
    result          TEXT,           -- no_answer/replied/interested/not_interested
    next_followup   TEXT,
    followup_date   TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_followups_buyer ON followups(buyer_id);
CREATE INDEX IF NOT EXISTS idx_followups_date ON followups(date);

-- ============================================================
-- 数据源配置表 (data_sources)
-- ============================================================
CREATE TABLE IF NOT EXISTS data_sources (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT UNIQUE NOT NULL,  -- volza/hunter/google/panjiva等
    display_name    TEXT,
    api_type        TEXT,           -- api/csv/scraper
    config          TEXT,           -- JSON: API keys, endpoints等
    enabled         INTEGER DEFAULT 1,
    priority        INTEGER DEFAULT 10,
    daily_limit     INTEGER,        -- 每日调用限制
    used_today      INTEGER DEFAULT 0,
    last_used       TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- 插入默认数据源
INSERT OR IGNORE INTO data_sources (name, display_name, api_type, config, priority) VALUES
('volza', 'Volza', 'csv', '{}', 10),
('google_maps', 'Google Maps API', 'api', '{}', 20),
('hunter', 'Hunter.io', 'api', '{}', 30),
('panjiva', 'Panjiva', 'csv', '{}', 40),
('importgenius', 'ImportGenius', 'csv', '{}', 50),
('linkedin', 'LinkedIn Sales Navigator', 'api', '{}', 60),
('zoominfo', 'ZoomInfo', 'api', '{}', 70),
('apollo', 'Apollo.io', 'api', '{}', 80),
('clearbit', 'Clearbit', 'api', '{}', 90),
('openai', 'OpenAI', 'api', '{}', 95),
('deepseek', 'DeepSeek', 'api', '{}', 96);

-- ============================================================
-- 导入批次表 (import_batches)
-- ============================================================
CREATE TABLE IF NOT EXISTS import_batches (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id        TEXT UNIQUE NOT NULL,
    source          TEXT,
    file_name       TEXT,
    file_path       TEXT,
    total_records   INTEGER DEFAULT 0,
    imported_records INTEGER DEFAULT 0,
    failed_records  INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'pending', -- pending/processing/completed/failed
    error_log       TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    completed_at    TEXT
);

-- ============================================================
-- API调用日志表 (api_logs)
-- ============================================================
CREATE TABLE IF NOT EXISTS api_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source          TEXT NOT NULL,
    endpoint        TEXT,
    method          TEXT,
    request_data    TEXT,
    response_status INTEGER,
    response_data   TEXT,
    error           TEXT,
    tokens_used     INTEGER,
    cost_usd        REAL,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_api_logs_source ON api_logs(source);
CREATE INDEX IF NOT EXISTS idx_api_logs_created ON api_logs(created_at);

-- ============================================================
-- AI提示词模板表 (ai_templates)
-- ============================================================
CREATE TABLE IF NOT EXISTS ai_templates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT UNIQUE NOT NULL,
    type            TEXT,           -- scoring/summary/outreach/cold_email等
    prompt_template TEXT NOT NULL,
    variables       TEXT,           -- JSON: 可用变量列表
    model           TEXT DEFAULT 'gpt-4o',
    temperature     REAL DEFAULT 0.7,
    max_tokens      INTEGER DEFAULT 500,
    enabled         INTEGER DEFAULT 1,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

-- 插入默认模板
INSERT OR IGNORE INTO ai_templates (name, type, prompt_template, variables, model) VALUES
('buyer_score', 'scoring', '请评估以下采购商的质量。\n\n公司名称: {{company_name}}\n国家: {{country}}\n行业: {{industry}}\n产品: {{products}}\n网站: {{website}}\n联系方式: {{has_contact}}\n进口记录: {{shipments}}\n\n请从以下维度评分:\n1. 是否真实采购商 (0-25分)\n2. 是否进口商/批发商 (0-25分)\n3. 采购能力评估 (0-20分)\n4. 联系方式质量 (0-15分)\n5. 国家风险 (0-15分)\n\n请返回JSON格式:\n{"score": 数字, "level": "A/B/C/D", "reasoning": "理由", "recommended_channel": "whatsapp/email/linkedin"}', '{{company_name}},{{country}},{{industry}},{{products}},{{website}},{{has_contact}},{{shipments}}', 'gpt-4o');

-- ============================================================
-- 系统配置表 (system_config)
-- ============================================================
CREATE TABLE IF NOT EXISTS system_config (
    key             TEXT PRIMARY KEY,
    value           TEXT,
    description     TEXT,
    updated_at      TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- 视图: 高价值采购商
-- ============================================================
CREATE VIEW IF NOT EXISTS v_top_buyers AS
SELECT 
    b.id, b.company_name, b.country, b.city, b.industry,
    b.products, b.website, b.email, b.phone, b.whatsapp, b.linkedin,
    b.source, b.ai_score, b.ai_level, b.buyer_type, b.risk_level, b.status,
    COUNT(DISTINCT sr.id) as shipment_count,
    COUNT(DISTINCT c.id) as contact_count,
    MAX(f.date) as last_followup
FROM buyers b
LEFT JOIN shipment_records sr ON b.id = sr.buyer_id
LEFT JOIN contacts c ON b.id = c.buyer_id
LEFT JOIN followups f ON b.id = f.buyer_id
WHERE b.status != 'blacklist'
GROUP BY b.id
ORDER BY b.ai_score DESC, shipment_count DESC;

-- ============================================================
-- 视图: 待跟进采购商
-- ============================================================
CREATE VIEW IF NOT EXISTS v_followup_due AS
SELECT 
    b.id, b.company_name, b.country, b.phone, b.whatsapp, b.email,
    b.ai_score, b.ai_level, b.status,
    f.next_followup, f.followup_date, f.result
FROM buyers b
JOIN followups f ON b.id = f.buyer_id
WHERE f.followup_date <= date('now', '+3 days')
    AND b.status NOT IN ('closed', 'blacklist')
ORDER BY f.followup_date ASC;
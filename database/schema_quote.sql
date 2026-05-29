-- 外贸轻ERP - 产品库 + 报价 + 订单 Schema

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ============================================================
-- 产品库 (products)
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name_cn         TEXT,               -- 中文名
    name_en         TEXT,               -- 英文名
    sku             TEXT UNIQUE,         -- SKU编码
    cost_price     REAL DEFAULT 0,      -- 成本价 (CNY)
    moq            INTEGER DEFAULT 100, -- 最小起订量
    unit           TEXT DEFAULT 'pcs',   -- 单位
    length_cm      REAL DEFAULT 0,       -- 长 (cm)
    width_cm       REAL DEFAULT 0,       -- 宽 (cm)
    height_cm      REAL DEFAULT 0,       -- 高 (cm)
    weight_kg      REAL DEFAULT 0,       -- 重量 (kg)
    volume_m3      REAL DEFAULT 0,       -- 体积 (立方米)
    profit_rate    REAL DEFAULT 30,      -- 利润率 (%)
    category       TEXT,                -- 分类
    description    TEXT,                -- 描述
    status         TEXT DEFAULT 'active', -- active/inactive
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- 客户/采购商关联订单 (customers - 复用buyers表)
-- 这里只存临时询价客户，不重复创建
-- ============================================================

-- ============================================================
-- 报价单 (quotations)
-- ============================================================
CREATE TABLE IF NOT EXISTS quotations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    quotation_no    TEXT UNIQUE NOT NULL, -- 报价单号 Q-YYYYMMDD-XXX
    buyer_id        INTEGER,              -- 关联采购商 (可选)
    buyer_name     TEXT,
    buyer_country  TEXT,
    buyer_phone    TEXT,
    buyer_email    TEXT,
    
    -- 产品明细 (JSON: [{product_id, name, quantity, unit_price, fob_price, cif_price}])
    items          TEXT,
    
    -- 价格汇总
    total_amount   REAL DEFAULT 0,       -- 总金额 (USD)
    price_term     TEXT DEFAULT 'FOB Shanghai', -- 价格条款
    currency       TEXT DEFAULT 'USD',
    
    -- 物流信息
    port_from      TEXT DEFAULT 'Shanghai',
    port_to        TEXT,
    shipping_method TEXT,              -- sea/air/express
    
    -- 付款方式
    payment_terms  TEXT DEFAULT '30% T/T in advance, 70% before shipment',
    
    -- 有效期
    valid_until    TEXT,                -- 有效期至
    
    -- 状态
    status         TEXT DEFAULT 'draft', -- draft/sent/confirmed/rejected/expired
    notes          TEXT,
    
    created_at     TEXT DEFAULT (datetime('now')),
    updated_at     TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- 订单 (orders) - 简化版
-- ============================================================
CREATE TABLE IF NOT EXISTS orders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no        TEXT UNIQUE NOT NULL, -- 订单号 OR-YYYYMMDD-XXX
    quotation_id    INTEGER,              -- 关联报价单
    buyer_id        INTEGER,              -- 采购商ID
    buyer_name     TEXT,
    buyer_country  TEXT,
    
    -- 产品
    items          TEXT,               -- JSON数组
    
    -- 金额
    total_amount   REAL DEFAULT 0,       -- 总金额 (USD)
    deposit_rate   REAL DEFAULT 30,      -- 定金比例
    deposit_paid   REAL DEFAULT 0,       -- 已付定金
    balance_paid   REAL DEFAULT 0,       -- 已付尾款
    
    -- 物流
    shipping_method TEXT,              -- sea/air/express
    port_from      TEXT DEFAULT 'Shanghai',
    port_to        TEXT,
    tracking_no    TEXT,                -- 运单号
    
    -- 状态
    status         TEXT DEFAULT 'inquiry', -- inquiry/quote/sample/payment/production/shipped/delivered/completed/cancelled
    
    -- 时间节点
    inquiry_date   TEXT,
    quote_date     TEXT,
    sample_date    TEXT,
    payment_date   TEXT,
    production_date TEXT,
    shipment_date  TEXT,
    delivery_date  TEXT,
    
    notes          TEXT,
    created_at     TEXT DEFAULT (datetime('now')),
    updated_at     TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- 运费配置 (shipping_rates)
-- ============================================================
CREATE TABLE IF NOT EXISTS shipping_rates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    country         TEXT NOT NULL,      -- 目的国
    port            TEXT,                -- 主要港口
    shipping_method TEXT NOT NULL,       -- sea/air/express
    rate_per_m3     REAL DEFAULT 0,      -- 每立方米运费 (USD)
    rate_per_kg     REAL DEFAULT 0,      -- 每公斤运费 (USD)
    min_charge      REAL DEFAULT 0,      -- 最低收费 (USD)
    transit_days    TEXT,                -- 运输天数
    notes           TEXT,
    updated_at      TEXT DEFAULT (datetime('now'))
);

-- 插入常用运费
INSERT OR IGNORE INTO shipping_rates (country, port, shipping_method, rate_per_m3, rate_per_kg, min_charge, transit_days) VALUES
('Nigeria', 'Lagos (Apapa)', 'sea', 600, 0.8, 100, '25-35 days'),
('Nigeria', 'Lagos (Apapa)', 'air', 3500, 3.5, 150, '7-10 days'),
('Ghana', 'Accra', 'sea', 550, 0.7, 100, '25-30 days'),
('Kenya', 'Mombasa', 'sea', 500, 0.6, 100, '20-30 days'),
('South Africa', 'Johannesburg (Durban)', 'sea', 450, 0.5, 100, '20-25 days'),
('UAE', 'Dubai', 'sea', 300, 0.4, 80, '10-15 days'),
('Saudi Arabia', 'Jeddah', 'sea', 350, 0.5, 80, '12-18 days'),
('Egypt', 'Cairo (Port Said)', 'sea', 400, 0.5, 80, '20-25 days'),
('Tanzania', 'Dar es Salaam', 'sea', 480, 0.6, 100, '25-30 days'),
('Malaysia', 'Kuala Lumpur (Port Klang)', 'sea', 250, 0.3, 60, '10-15 days'),
('Indonesia', 'Jakarta', 'sea', 280, 0.35, 60, '12-18 days'),
('Vietnam', 'Ho Chi Minh City', 'sea', 260, 0.3, 60, '10-15 days'),
('Philippines', 'Manila', 'sea', 270, 0.32, 60, '12-18 days'),
('Pakistan', 'Karachi', 'sea', 300, 0.4, 80, '15-20 days'),
('India', 'Mumbai', 'sea', 280, 0.35, 60, '15-20 days');

-- ============================================================
-- 港口配置 (ports)
-- ============================================================
CREATE TABLE IF NOT EXISTS ports (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    country         TEXT NOT NULL,
    port_name       TEXT NOT NULL,
    port_code       TEXT,
    is_main         INTEGER DEFAULT 0,   -- 是否主要港口
    UNIQUE(country, port_name)
);

INSERT OR IGNORE INTO ports (country, port_name, port_code, is_main) VALUES
('China', 'Shanghai', 'SHA', 1),
('China', 'Ningbo', 'NGB', 0),
('China', 'Shenzhen', 'SZX', 0),
('China', 'Guangzhou', 'CAN', 0),
('Nigeria', 'Lagos (Apapa)', 'LOS', 1),
('Nigeria', 'Port Harcourt', 'PHC', 0),
('Ghana', 'Accra', 'ACC', 1),
('Kenya', 'Mombasa', 'MBA', 1),
('South Africa', 'Durban', 'DUR', 1),
('South Africa', 'Cape Town', 'CPT', 0),
('UAE', 'Dubai (Jebel Ali)', 'DXB', 1),
('Saudi Arabia', 'Jeddah', 'JED', 1),
('Egypt', 'Port Said', 'PSD', 1),
('Tanzania', 'Dar es Salaam', 'DAR', 1),
('Malaysia', 'Kuala Lumpur (Port Klang)', 'PKL', 1),
('Indonesia', 'Jakarta', 'JKT', 1),
('Vietnam', 'Ho Chi Minh City', 'SGN', 1),
('Philippines', 'Manila', 'MNL', 1),
('Pakistan', 'Karachi', 'KHI', 1),
('India', 'Mumbai', 'BOM', 1);

-- ============================================================
-- 公司配置 (company_info)
-- ============================================================
CREATE TABLE IF NOT EXISTS company_info (
    id              INTEGER PRIMARY KEY,
    company_name_cn TEXT,
    company_name_en TEXT,
    address         TEXT,
    phone           TEXT,
    email           TEXT,
    website         TEXT,
    whatsapp        TEXT,
    bank_info       TEXT,               -- 银行信息
    updated_at      TEXT DEFAULT (datetime('now'))
);

-- 插入默认公司信息
INSERT OR IGNORE INTO company_info (id, company_name_en, whatsapp, updated_at) VALUES
(1, 'Yiwu Grace Trading Co.', 'https://wa.me/your_whatsapp', datetime('now'));

-- ============================================================
-- 产品样例数据
-- ============================================================
INSERT OR IGNORE INTO products (name_cn, name_en, sku, cost_price, moq, length_cm, width_cm, height_cm, weight_kg, profit_rate, category) VALUES
('防紫外线发帽', 'UV Protection Hair Bonnet', 'UV-HB-001', 8, 100, 20, 15, 5, 0.1, 35, 'Hair Accessories'),
('丝绸发帽', 'Silk Hair Bonnet', 'SH-HB-002', 12, 100, 20, 15, 5, 0.1, 35, 'Hair Accessories'),
('发夹套装', 'Hair Clips Set', 'HC-SET-001', 5, 200, 15, 10, 3, 0.05, 40, 'Hair Accessories'),
('发圈套装', 'Hair Bands Set', 'HB-SET-001', 4, 300, 12, 8, 3, 0.03, 40, 'Hair Accessories'),
('防晒衣', 'UV Protection Clothing', 'UV-CC-001', 25, 50, 40, 30, 2, 0.3, 45, 'Clothing'),
('发箍', 'Hair Headband', 'HH-HB-001', 3, 500, 18, 5, 2, 0.02, 40, 'Hair Accessories'),
('时尚项链', 'Fashion Necklace', 'FN-NL-001', 6, 200, 20, 15, 2, 0.05, 50, 'Jewelry'),
('手镯套装', 'Bracelet Set', 'BR-ST-001', 4, 300, 15, 10, 2, 0.04, 50, 'Jewelry');
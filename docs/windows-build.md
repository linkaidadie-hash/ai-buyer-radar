# AI Buyer Radar - Windows 桌面版架构

## 核心需求
1. AI常驻运行（系统托盘）
2. API接口供其他程序调用
3. 浏览器界面（可选）

## 技术方案

### 1. PyInstaller 打包 (推荐)
- Python后端 + 内嵌HTML前端
- 系统托盘运行
- 无需管理员权限

### 2. 目录结构
```
buyer-radar-win/
├── buyer-radar.exe        # 主程序
├── database/
│   └── buyers.db          # SQLite数据库
├── config.json            # 配置文件
├── README.txt
└── logs/
    └── app.log            # 日志
```

### 3. 系统托盘功能
- 双击打开主界面
- 右键菜单：
  - 打开主界面
  - 快速报价
  - 采购商查询
  - API状态
  - 退出

### 4. API接口 (供其他程序调用)
```
GET  http://localhost:8001/api/quote/products          # 产品列表
POST http://localhost:8001/api/quote/calculate         # 计算报价
POST http://localhost:quote/quotations                  # 生成报价单
GET  http://localhost:8001/api/buyers                  # 采购商列表
POST http://localhost:8001/api/ai/score                # AI评分
POST http://localhost:8001/api/ai/outreach            # 生成联系话术
```

### 5. 其他程序接入示例

#### Python调用
```python
import requests
response = requests.post('http://localhost:8001/api/quote/calculate', json={
    'items': [{'product_id': 1, 'quantity': 500}],
    'country': 'Nigeria',
    'shipping_method': 'sea'
})
print(response.json())
```

#### Excel VBA调用
```vba
' Excel中调用报价API
Function GetQuote(productId As Long, qty As Long, country As String)
    Dim http As Object
    Set http = CreateObject("MSXML2.XMLHTTP")
    http.Open "POST", "http://localhost:8001/api/quote/calculate", False
    http.setRequestHeader "Content-Type", "application/json"
    http.Send "{...}"
    GetQuote = http.ResponseText
End Function
```

#### C# 调用
```csharp
var client = new HttpClient();
var response = await client.PostAsJsonAsync("http://localhost:8001/api/quote/calculate", data);
```

### 6. 开机自启动
- 注册表 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
- 或 启动菜单快捷方式

## 文件清单

### 必需文件
- buyer-radar.exe
- buyer-radar.db (首次运行自动创建)
- config.json (配置)

### 可选文件
- products_import.xlsx (批量导入产品)
- buyers_export.xlsx (导出采购商)

## 构建步骤

### 1. 安装依赖
```bash
pip install pyinstaller fastapi uvicorn aiohttp beautifulsoup4 lxml playwright
playwright install chromium
```

### 2. 构建命令
```bash
pyinstaller --onefile --noconsole --icon=app.ico ^
    --add-data "database;database" ^
    --add-data "frontend;frontend" ^
    --hidden-import=uvicorn --hidden-import=fastapi ^
    --hidden-import=sqlite3 --hidden-import=ai_service ^
    --name "AI-Buyer-Radar" main.spec
```

### 3. 配置托盘
使用 `pystray` + `Pillow` 实现系统托盘

## 注意事项
- 首次运行需要联网激活
- 端口8001需保持空闲
- 数据库文件不要删除
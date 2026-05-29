# AI Buyer Radar - Windows 桌面版

## 快速开始

### 1. 双击运行
```
双击 "启动AI雷达.bat" 即可启动
```

### 2. 功能说明
- 📦 **产品库管理** - 添加/编辑产品，设置成本和MOQ
- 🔮 **AI智能报价** - FOB/CIF/DDP自动计算
- 📄 **报价单生成** - 一键生成专业报价单
- 📋 **订单管理** - 轻量订单跟踪
- 👥 **采购商管理** - AI评分和跟进

### 3. API接口 (供其他程序调用)

启动后自动开启API服务在其他程序中调用：

```
# 报价计算
POST http://localhost:8001/api/quote/calculate
Content-Type: application/json

{
  "items": [{"product_id": 1, "quantity": 500}],
  "country": "Nigeria",
  "shipping_method": "sea"
}

# 产品列表
GET http://localhost:8001/api/quote/products

# 生成报价单
POST http://localhost:8001/api/quote/quotations
Content-Type: application/json

{
  "buyer_name": "ABC Trading",
  "buyer_country": "Nigeria",
  "items": [{"product_id": 1, "quantity": 500}],
  "country": "Nigeria",
  "shipping_method": "sea"
}
```

### 4. 系统托盘
- 启动后在右下角系统托盘显示图标
- 右键点击可快速访问各项功能
- 关闭窗口时最小化到托盘（不退出程序）

### 5. 其他程序接入示例

**Python:**
```python
import requests
r = requests.post('http://localhost:8001/api/quote/calculate', json={
    'items': [{'product_id': 1, 'quantity': 500}],
    'country': 'Nigeria', 'shipping_method': 'sea'
})
print(r.json())
```

**Excel VBA:**
```vba
Function GetQuote(productId As Long, qty As Long)
    Dim xmlhttp As Object
    Set xmlhttp = CreateObject("MSXML2.XMLHTTP")
    xmlhttp.Open "POST", "http://localhost:8001/api/quote/calculate", False
    xmlhttp.setRequestHeader "Content-Type", "application/json"
    xmlhttp.Send "{""items"":[{""product_id"":1,""quantity"":" & qty & "}]," & _
                 """country"":""Nigeria"",""shipping_method"":""sea""}"
    GetQuote = xmlhttp.ResponseText
End Function
```

**C# / .NET:**
```csharp
var client = new HttpClient();
var content = new StringContent(jsonString, Encoding.UTF8, "application/json");
var response = await client.PostAsync("http://localhost:8001/api/quote/calculate", content);
var result = await response.Content.ReadAsStringAsync();
```

**PHP:**
```php
$response = file_get_contents('http://localhost:8001/api/quote/products');
$data = json_decode($response, true);
```

### 6. 端口说明
- 默认端口: **8001**
- API文档: http://localhost:8001/docs
- 前端界面: http://localhost:8001

### 7. 数据存储
- 数据库: `database/buyers.db` (SQLite)
- 配置文件: `config.json`
- 日志文件: `logs/app.log`

### 8. 常见问题

**端口被占用?**
修改 `config.json` 中的 `api_port` 为其他端口

**无法启动?**
检查是否已安装 Python 3.8+
命令行运行: `pip install -r requirements.txt`

### 9. 技术支持
AI Buyer Radar - 外贸获客 + 智能报价系统
Version 1.0.0
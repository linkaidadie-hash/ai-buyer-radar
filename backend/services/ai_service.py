"""
AI评分服务
核心价值：判断真实采购商、AI评分、AI分类
"""
import json
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime


class AIScorer:
    """AI采购商评分"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # AI提供商配置
        self.openai_key = config.get('openai_key')
        self.deepseek_key = config.get('deepseek_key')
        self.default_model = config.get('model', 'gpt-4o')
        self.temperature = config.get('temperature', 0.3)  # 低温度保证一致性
    
    def score_buyer(self, buyer: Dict[str, Any]) -> Dict[str, Any]:
        """
        对采购商进行AI评分
        返回: {score, level, reasoning, recommended_channel, risk_level}
        """
        prompt = self._build_score_prompt(buyer)
        
        # 调用AI
        response = self._call_ai(prompt)
        
        if response:
            return self._parse_score_response(response)
        
        # fallback: 基础评分
        return self._basic_score(buyer)
    
    def batch_score(self, buyers: List[Dict[str, Any]], 
                    progress_callback=None) -> Dict[int, Dict[str, Any]]:
        """
        批量评分
        :param buyers: [(id, data), ...]
        :param progress_callback: 进度回调
        """
        results = {}
        total = len(buyers)
        
        for i, (buyer_id, buyer) in enumerate(buyers):
            try:
                score_result = self.score_buyer(buyer)
                results[buyer_id] = score_result
            except Exception as e:
                print(f"[AI] Score buyer {buyer_id} failed: {e}")
                results[buyer_id] = {'score': 50, 'level': 'C', 'reasoning': '评分失败'}
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        return results
    
    def _build_score_prompt(self, buyer: Dict[str, Any]) -> str:
        """构建评分Prompt"""
        
        # 联系方式质量
        has_contact = []
        if buyer.get('email'): has_contact.append('邮箱')
        if buyer.get('phone'): has_contact.append('电话')
        if buyer.get('whatsapp'): has_contact.append('WhatsApp')
        if buyer.get('linkedin'): has_contact.append('LinkedIn')
        has_contact_str = '、'.join(has_contact) if has_contact else '无'
        
        # 进口记录
        shipments = buyer.get('shipments', [])
        shipment_info = f"共{len(shipments)}条进口记录" if shipments else '无进口记录'
        
        prompt = f"""你是一个专业的B2B采购商评估专家。请评估以下采购商的质量。

## 采购商信息
公司名称: {buyer.get('company_name', '未知')}
国家: {buyer.get('country', '未知')}
城市: {buyer.get('city', '未知')}
行业: {buyer.get('industry', '未知')}
主营产品: {buyer.get('products', '未知')}
网站: {buyer.get('website', '无')}
联系方式: {has_contact_str}
进口记录: {shipment_info}
数据来源: {buyer.get('source', '未知')}

## 评分维度（总分100分）
1. 是否真实采购商 (0-25分)
   - 有真实业务实体为采购商得20-25分
   - 可能是采购商得10-19分
   - 难以判断得0-9分
   
2. 是否进口商/批发商 (0-25分)
   - 明确是进口商/批发商得20-25分
   - 可能是得10-19分
   - 零售商/终端客户得0-9分
   
3. 采购能力评估 (0-20分)
   - 进口记录多、产品匹配得15-20分
   - 有进口记录但产品不明确得5-14分
   - 无进口记录得0-4分
   
4. 联系方式质量 (0-15分)
   - 邮箱+电话+社交媒体齐全得12-15分
   - 有邮箱或电话得6-11分
   - 仅网站或无联系方式得0-5分
   
5. 国家风险 (0-15分)
   - 低风险国家(欧美日韩中东)得12-15分
   - 中等风险国家(中国/印度/东南亚)得6-11分
   - 高风险或信息不足得0-5分

## 输出要求
请返回JSON格式结果，不要返回其他内容：
{{
    "score": 数字(0-100),
    "level": "A/B/C/D",
    "reasoning": "评分理由，简短说明",
    "recommended_channel": "whatsapp/email/linkedin/call",
    "risk_level": "low/medium/high",
    "buyer_type": "真实进口商/批发商/分销商/不确定"
}}

等级定义：
- A级(80-100分): 优先跟进
- B级(60-79分): 重点跟进  
- C级(40-59分): 普通跟进
- D级(0-39分): 暂不跟进"""
        
        return prompt
    
    def _call_ai(self, prompt: str, model: str = None) -> Optional[str]:
        """调用AI服务"""
        
        # 优先使用OpenAI
        if self.openai_key:
            return self._call_openai(prompt, model or 'gpt-4o')
        
        # 备用DeepSeek
        if self.deepseek_key:
            return self._call_deepseek(prompt, model or 'deepseek-chat')
        
        return None
    
    def _call_openai(self, prompt: str, model: str = 'gpt-4o') -> Optional[str]:
        """调用OpenAI"""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            'Authorization': f'Bearer {self.openai_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': self.temperature,
            'max_tokens': 500,
        }
        
        try:
            resp = httpx.post(url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"[AI] OpenAI call failed: {e}")
        return None
    
    def _call_deepseek(self, prompt: str, model: str = 'deepseek-chat') -> Optional[str]:
        """调用DeepSeek"""
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            'Authorization': f'Bearer {self.deepseek_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': self.temperature,
            'max_tokens': 500,
        }
        
        try:
            resp = httpx.post(url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"[AI] DeepSeek call failed: {e}")
        return None
    
    def _parse_score_response(self, response: str) -> Dict[str, Any]:
        """解析AI评分响应"""
        try:
            # 尝试提取JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                result = json.loads(json_str)
                
                # 验证和标准化
                return {
                    'score': max(0, min(100, int(result.get('score', 50)))),
                    'level': result.get('level', 'C'),
                    'reasoning': result.get('reasoning', ''),
                    'recommended_channel': result.get('recommended_channel', 'email'),
                    'risk_level': result.get('risk_level', 'medium'),
                    'buyer_type': result.get('buyer_type', '不确定'),
                }
        except Exception as e:
            print(f"[AI] Parse response failed: {e}")
        
        return {'score': 50, 'level': 'C', 'reasoning': '解析失败', 
                'recommended_channel': 'email', 'risk_level': 'medium'}
    
    def _basic_score(self, buyer: Dict[str, Any]) -> Dict[str, Any]:
        """基础评分（无AI时fallback）"""
        score = 50
        
        # 有进口记录 +10
        if buyer.get('shipments'):
            score += 10
        
        # 有详细联系方式 +10
        contact_count = sum([
            bool(buyer.get('email')),
            bool(buyer.get('phone')),
            bool(buyer.get('whatsapp')),
        ])
        score += contact_count * 5
        
        # 有网站 +5
        if buyer.get('website'):
            score += 5
        
        # 产品匹配 +5
        if buyer.get('products'):
            score += 5
        
        # 计算等级
        level = 'D'
        if score >= 80:
            level = 'A'
        elif score >= 60:
            level = 'B'
        elif score >= 40:
            level = 'C'
        
        return {
            'score': min(100, score),
            'level': level,
            'reasoning': '基于基础规则评分',
            'recommended_channel': 'email',
            'risk_level': 'medium',
        }


# ============================================================
# AI联系话术生成
# ============================================================

class AIOutreachGenerator:
    """AI联系话术生成"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.openai_key = config.get('openai_key')
        self.deepseek_key = config.get('deepseek_key')
    
    def generate_email(self, buyer: Dict[str, Any], product: str = None,
                       language: str = 'en') -> str:
        """生成开发邮件"""
        
        product = product or buyer.get('products', ['your products'])[0] if buyer.get('products') else 'products'
        
        prompt = f"""请为以下采购商生成一封专业的英文开发信。

## 采购商信息
公司: {buyer.get('company_name', '')}
国家: {buyer.get('country', '')}
主营产品: {buyer.get('products', '')}
采购商类型: {buyer.get('buyer_type', 'Importer')}

## 产品
{product}

## 要求
1. 专业、简洁、不俗气
2. 突出中国供应商优势
3. 包含明确的行动号召(CTA)
4. 适合首次联系
5. 邮件长度控制在100-150词
6. 使用{{company_name}}作为公司名称占位符

## 输出
只返回邮件正文内容，不需要主题行。"""
        
        if language != 'en':
            prompt += f"\n请使用{language}语言书写。"
        
        return self._call_ai(prompt)
    
    def generate_whatsapp(self, buyer: Dict[str, Any], 
                          product: str = None, language: str = 'en') -> str:
        """生成WhatsApp消息"""
        
        product = product or buyer.get('products', [''])[0]
        
        prompt = f"""请为以下采购商生成一条WhatsApp短消息。

## 采购商信息
公司: {buyer.get('company_name', '')}
国家: {buyer.get('country', '')}

## 产品
{product}

## 要求
1. 简短友好，30-50词
2. 表明身份和产品优势
3. 询问是否感兴趣
4. 留下联系方式
5. 使用{{company_name}}作为公司名称占位符"""
        
        if language != 'en':
            prompt += f"\n请使用{language}语言书写。"
        
        return self._call_ai(prompt)
    
    def generate_linkedin_request(self, buyer: Dict[str, Any], 
                                   product: str = None, language: str = 'en') -> Dict[str, str]:
        """生成LinkedIn连接请求"""
        
        product = product or buyer.get('products', [''])[0]
        
        prompt = f"""请为以下采购商生成LinkedIn连接请求和消息。

## 采购商信息
公司: {buyer.get('company_name', '')}
国家: {buyer.get('country', '')}

## 产品
{product}

## 输出要求
返回JSON格式：
{{
    "request_note": "连接请求附言，300字符以内",
    "message": "发送的消息内容，100词以内"
}}

要求：
1. 专业友好
2. 说明连接原因
3. 表明合作意向
4. 使用{{company_name}}作为公司名称占位符"""
        
        if language != 'en':
            prompt += f"\n请使用{language}语言书写。"
        
        response = self._call_ai(prompt)
        if response:
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                return json.loads(response[start:end])
            except:
                pass
        
        return {'request_note': f'Hi, I represent a manufacturer of {product}.', 
                'message': f'We supply {product} to global buyers.'}
    
    def generate_followup(self, buyer: Dict[str, Any], 
                          channel: str = 'email', language: str = 'en') -> str:
        """生成跟进话术"""
        
        prompt = f"""请生成一条针对以下采购商的{channel}跟进消息。

## 采购商信息
公司: {buyer.get('company_name', '')}
国家: {buyer.get('country', '')}
买家类型: {buyer.get('buyer_type', '')}

## 跟进渠道
{channel}

## 要求
1. 友好但不卑微
2. 提醒之前的联系
3. 提供价值（如新产品、市场动态）
4. 询问是否需要报价
5. 适合第2-3次跟进
6. 长度适中"""
        
        if language != 'en':
            prompt += f"\n请使用{language}语言书写。"
        
        return self._call_ai(prompt)
    
    def _call_ai(self, prompt: str) -> Optional[str]:
        """调用AI"""
        if self.openai_key:
            return self._call_openai(prompt)
        if self.deepseek_key:
            return self._call_deepseek(prompt)
        return None
    
    def _call_openai(self, prompt: str) -> Optional[str]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            'Authorization': f'Bearer {self.openai_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': 'gpt-4o',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.7,
            'max_tokens': 800,
        }
        
        try:
            resp = httpx.post(url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"[AI] OpenAI call failed: {e}")
        return None
    
    def _call_deepseek(self, prompt: str) -> Optional[str]:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            'Authorization': f'Bearer {self.deepseek_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': 'deepseek-chat',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.7,
            'max_tokens': 800,
        }
        
        try:
            resp = httpx.post(url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"[AI] DeepSeek call failed: {e}")
        return None
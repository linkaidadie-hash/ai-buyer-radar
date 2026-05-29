"""
Hunter.io 数据源适配器
邮箱提取、邮箱猜测、邮箱验证
https://hunter.io/
"""
import httpx
from typing import List, Dict, Any, Optional
from .base import BaseDataSource, BuyerData


class HunterSource(BaseDataSource):
    """Hunter.io 邮箱数据源"""
    
    name = "hunter"
    display_name = "Hunter.io"
    api_type = "api"
    max_per_page = 100
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = self.config.get('api_key')
        self.base_url = "https://api.hunter.io/v2"
    
    def search(self, keyword: str, country: str = None, 
               limit: int = 100, **kwargs) -> List[BuyerData]:
        """Hunter主要通过公司域名搜索邮箱，不支持产品关键词搜索"""
        return []
    
    def find_email(self, company_name: str, domain: str = None, 
                   first_name: str = None, last_name: str = None) -> Optional[Dict]:
        """
        搜索公司邮箱
        :return: {'email': '...', 'score': 80, 'verified': True}
        """
        if not self.api_key:
            return None
        
        # 方式1: 域名搜索
        if domain:
            return self._domain_search(domain)
        
        # 方式2: 公司名搜索
        if company_name:
            return self._company_search(company_name, country)
        
        return None
    
    def _domain_search(self, domain: str) -> Optional[Dict]:
        """域名搜索"""
        url = f"{self.base_url}/domain-search"
        params = {'api_key': self.api_key, 'domain': domain, 'limit': 10}
        
        try:
            resp = httpx.get(url, params=params, timeout=30)
            data = resp.json()
            
            emails = data.get('data', {}).get('emails', [])
            if emails:
                primary = emails[0]
                return {
                    'email': primary.get('value'),
                    'score': primary.get('confidence', 0),
                    'verified': primary.get('verification', {}).get('status') == 'valid',
                    'type': primary.get('type'),  # personal/generic
                    'position': primary.get('position'),
                    'department': primary.get('department'),
                }
        except Exception as e:
            print(f"[Hunter] Domain search failed: {e}")
        return None
    
    def _company_search(self, company: str, country: str = None) -> Optional[Dict]:
        """公司搜索"""
        url = f"{self.base_url}/company-search"
        params = {'api_key': self.api_key, 'name': company}
        if country:
            params['country'] = country
        
        try:
            resp = httpx.get(url, params=params, timeout=30)
            data = resp.json()
            
            result = data.get('data', {})
            if result.get('domain'):
                domain_result = self._domain_search(result['domain'])
                if domain_result:
                    return domain_result
        except Exception as e:
            print(f"[Hunter] Company search failed: {e}")
        return None
    
    def verify_email(self, email: str) -> bool:
        """验证邮箱"""
        if not self.api_key:
            return False
        
        url = f"{self.base_url}/email-verifier"
        params = {'api_key': self.api_key, 'email': email}
        
        try:
            resp = httpx.get(url, params=params, timeout=30)
            data = resp.json()
            result = data.get('data', {})
            return result.get('status') == 'valid'
        except:
            return False
    
    def enrich_buyer(self, buyer: BuyerData) -> BuyerData:
        """补充采购商邮箱信息"""
        if buyer.email:
            return buyer
        
        if buyer.website:
            domain = buyer.website.replace('https://', '').replace('http://', '').replace('www.', '')
            email_info = self.find_email(buyer.company_name, domain)
            if email_info and email_info.get('email'):
                buyer.email = email_info['email']
        
        return buyer
    
    def get_company_details(self, company_id: str) -> Optional[BuyerData]:
        return None
    
    def validate_config(self) -> tuple[bool, str]:
        if not self.api_key:
            return False, "Hunter.io API Key未配置"
        return True, "OK"


# ============================================================
# Panjiva 数据源 (S&P Global)
# ============================================================

class PanjivaSource(BaseDataSource):
    """Panjiva 美国进口数据"""
    
    name = "panjiva"
    display_name = "Panjiva"
    api_type = "csv"
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = self.config.get('api_key')
    
    def search(self, keyword: str, country: str = None, 
               limit: int = 100, **kwargs) -> List[BuyerData]:
        """Panjiva主要通过CSV导入，不支持实时搜索"""
        return []
    
    def parse_csv_data(self, csv_data: List[Dict[str, Any]]) -> List[BuyerData]:
        """
        解析Panjiva导出的CSV
        字段：Company, City, State, Country, Product, HS Code, 
              Shipment Count, Supplier, Date, Quantity, Value
        """
        buyers = {}
        
        for row in csv_data:
            company = row.get('Company') or row.get('company_name', '')
            if not company:
                continue
            
            key = company.lower().strip()
            if key not in buyers:
                buyers[key] = BuyerData(
                    company_name=company,
                    country=row.get('Country', ''),
                    city=row.get('City', ''),
                    products=[],
                    hs_code=[],
                    source=self.name,
                )
            
            product = row.get('Product', '')
            if product and product not in buyers[key].products:
                buyers[key].products.append(product)
            
            hs = row.get('HS Code', '')
            if hs and hs not in buyers[key].hs_code:
                buyers[key].hs_code.append(hs)
        
        return list(buyers.values())
    
    def get_company_details(self, company_id: str) -> Optional[BuyerData]:
        return None


# ============================================================
# ImportGenius 数据源
# ============================================================

class ImportGeniusSource(BaseDataSource):
    """ImportGenius 全球贸易数据"""
    
    name = "importgenius"
    display_name = "ImportGenius"
    api_type = "csv"
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
    
    def search(self, keyword: str, country: str = None, 
               limit: int = 100, **kwargs) -> List[BuyerData]:
        return []
    
    def parse_csv_data(self, csv_data: List[Dict[str, Any]]) -> List[BuyerData]:
        """ImportGenius CSV解析"""
        buyers = {}
        
        for row in csv_data:
            # 尝试多种可能的字段名
            company = (row.get('Buyer') or row.get('Importer') or 
                      row.get('Company') or row.get('company_name', ''))
            if not company:
                continue
            
            key = company.lower().strip()
            if key not in buyers:
                buyers[key] = BuyerData(
                    company_name=company,
                    country=row.get('Country', ''),
                    city=row.get('City', ''),
                    products=[],
                    source=self.name,
                )
            
            product = row.get('Product', '')
            if product:
                buyers[key].products.append(product)
        
        return list(buyers.values())
    
    def get_company_details(self, company_id: str) -> Optional[BuyerData]:
        return None


# ============================================================
# LinkedIn Sales Navigator
# ============================================================

class LinkedInSource(BaseDataSource):
    """LinkedIn采购负责人"""
    
    name = "linkedin"
    display_name = "LinkedIn Sales Navigator"
    api_type = "api"
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.client_id = self.config.get('client_id')
        self.client_secret = self.config.get('client_secret')
    
    def search(self, keyword: str, country: str = None, 
               limit: int = 100, **kwargs) -> List[BuyerData]:
        """
        LinkedIn主要通过公司名搜索相关采购负责人
        注意：LinkedIn API限制严格，实际对接需申请Partner权限
        """
        if not self.client_id:
            return []
        
        # 实现预留，实际需要OAuth和Partner申请
        return []
    
    def get_contacts(self, company_name: str) -> List[Dict]:
        """获取公司联系人"""
        # 需要LinkedIn API权限
        return []
    
    def get_company_details(self, company_id: str) -> Optional[BuyerData]:
        return None
    
    def validate_config(self) -> tuple[bool, str]:
        if not self.client_id:
            return False, "LinkedIn Client ID未配置"
        return True, "OK"


# ============================================================
# ZoomInfo 数据源
# ============================================================

class ZoomInfoSource(BaseDataSource):
    """ZoomInfo 企业联系信息"""
    
    name = "zoominfo"
    display_name = "ZoomInfo"
    api_type = "api"
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = self.config.get('api_key')
        self.base_url = "https://api.zoominfo.com"
    
    def search(self, keyword: str, country: str = None, 
               limit: int = 100, **kwargs) -> List[BuyerData]:
        if not self.api_key:
            return []
        
        # ZoomInfo Enrich API
        url = f"{self.base_url}/enrich/company"
        headers = {'Authorization': f'Bearer {self.api_key}'}
        payload = {'companyName': keyword}
        if country:
            payload['country'] = country
        
        try:
            resp = httpx.post(url, json=payload, headers=headers, timeout=30)
            data = resp.json()
            return self._parse_response(data)
        except Exception as e:
            print(f"[ZoomInfo] Search failed: {e}")
            return []
    
    def _parse_response(self, data: Dict) -> List[BuyerData]:
        """解析ZoomInfo响应"""
        results = []
        companies = data.get('data', [])
        
        for co in companies:
            buyer = BuyerData(
                company_name=co.get('companyName', ''),
                country=co.get('address', {}).get('country'),
                city=co.get('address', {}).get('city'),
                industry=co.get('industry'),
                website=co.get('companyWebsite'),
                phone=co.get('phoneNumber'),
                email=co.get('email'),
                source=self.name,
            )
            results.append(buyer)
        
        return results
    
    def get_company_details(self, company_id: str) -> Optional[BuyerData]:
        return None
    
    def validate_config(self) -> tuple[bool, str]:
        if not self.api_key:
            return False, "ZoomInfo API Key未配置"
        return True, "OK"


# ============================================================
# Apollo.io 数据源
# ============================================================

class ApolloSource(BaseDataSource):
    """Apollo.io 企业+邮箱数据"""
    
    name = "apollo"
    display_name = "Apollo.io"
    api_type = "api"
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = self.config.get('api_key')
        self.base_url = "https://api.apollo.io/v1"
    
    def _headers(self) -> Dict[str, str]:
        return {'X-Api-Key': self.api_key} if self.api_key else {}
    
    def search(self, keyword: str, country: str = None, 
               limit: int = 100, **kwargs) -> List[BuyerData]:
        """组织搜索 - 使用 /accounts/search"""
        if not self.api_key:
            return []
        
        url = f"{self.base_url}/accounts/search"
        params = {
            'q': keyword,
            'per_page': min(limit, 50),
        }
        if country:
            params['countries'] = [country.upper()]
        
        try:
            resp = httpx.get(url, params=params, headers=self._headers(), timeout=30)
            data = resp.json()
            return self._parse_accounts(data)
        except Exception as e:
            print(f"[Apollo] Search failed: {e}")
            return []
    
    def find_contacts(self, organization_name: str = None, domain: str = None) -> List[Dict]:
        """获取公司联系人 - 使用 /contacts/search"""
        if not self.api_key:
            return []
        
        url = f"{self.base_url}/contacts/search"
        params = {'per_page': 10}
        if organization_name:
            params['q_organization_name'] = organization_name
        if domain:
            params['q_organization_name'] = domain.replace('www.', '')
        
        try:
            resp = httpx.get(url, params=params, headers=self._headers(), timeout=30)
            data = resp.json()
            return data.get('contacts', [])
        except:
            return []
    
    def _parse_accounts(self, data: Dict) -> List[BuyerData]:
        """解析账户/组织数据"""
        results = []
        accounts = data.get('accounts', []) or data.get('organizations', []) or []
        
        for acc in accounts:
            buyer = BuyerData(
                company_name=acc.get('name', '') or acc.get('organization_name', ''),
                country=acc.get('country') or acc.get('location', {}).get('country'),
                city=acc.get('city') or acc.get('location', {}).get('city'),
                industry=acc.get('industry'),
                website=acc.get('website_url') or acc.get('domain'),
                linkedin=acc.get('linkedin_url'),
                source=self.name,
            )
            results.append(buyer)
        
        return results
    
    def enrich_buyer(self, buyer: BuyerData) -> BuyerData:
        """补全企业信息 - 通过域名找联系人获取邮箱"""
        if not buyer.email and buyer.website:
            domain = buyer.website.replace('https://', '').replace('http://', '').replace('www.', '')
            contacts = self.find_contacts(domain=domain)
            for c in contacts:
                email = c.get('email')
                if email:
                    buyer.email = email
                    break
        return buyer
    
    def get_company_details(self, company_id: str) -> Optional[BuyerData]:
        return None
    
    def validate_config(self) -> tuple[bool, str]:
        if not self.api_key:
            return False, "Apollo.io API Key未配置"
        return True, "OK"


# ============================================================
# Clearbit 数据源
# ============================================================

class ClearbitSource(BaseDataSource):
    """Clearbit 企业数据补全"""
    
    name = "clearbit"
    display_name = "Clearbit"
    api_type = "api"
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = self.config.get('api_key')
        self.base_url = "https://company.clearbit.com/v2"
    
    def search(self, keyword: str, country: str = None, 
               limit: int = 100, **kwargs) -> List[BuyerData]:
        """Clearbit主要做企业补全，不做搜索"""
        return []
    
    def enrich_buyer(self, buyer: BuyerData) -> BuyerData:
        """补全企业信息"""
        if not self.api_key:
            return buyer
        
        # 通过公司名补全
        url = f"{self.base_url}/companies/find"
        params = {'name': buyer.company_name}
        headers = {'Authorization': f'Bearer {self.api_key}'}
        
        try:
            resp = httpx.get(url, params=params, headers=headers, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                buyer.website = buyer.website or data.get('website')
                buyer.industry = buyer.industry or data.get('industry')
                buyer.linkedin = buyer.linkedin or data.get('linkedin', {}).get('handle')
                
                metrics = data.get('metrics', {})
                if metrics:
                    buyer.metrics = metrics
        except Exception as e:
            print(f"[Clearbit] Enrich failed: {e}")
        
        return buyer
    
    def get_company_details(self, company_id: str) -> Optional[BuyerData]:
        return None
    
    def validate_config(self) -> tuple[bool, str]:
        if not self.api_key:
            return False, "Clearbit API Key未配置"
        return True, "OK"


# ============================================================
# 数据源注册表
# ============================================================

def get_all_sources() -> Dict[str, type]:
    """获取所有可用数据源"""
    return {
        'volza': VolzaSource,
        'google_maps': GoogleMapsSource,
        'hunter': HunterSource,
        'panjiva': PanjivaSource,
        'importgenius': ImportGeniusSource,
        'linkedin': LinkedInSource,
        'zoominfo': ZoomInfoSource,
        'apollo': ApolloSource,
        'clearbit': ClearbitSource,
    }


def create_source(name: str, config: Dict = None) -> Optional[BaseDataSource]:
    """创建数据源实例"""
    sources = get_all_sources()
    source_class = sources.get(name)
    if source_class:
        return source_class(config)
    return None

# ============================================================
# Snov.io 数据源
# ============================================================

class SnovSource(BaseDataSource):
    """Snov.io 邮箱查找+验证
    官方文档: https://snov.io/api
    OAuth2认证，token有效期1小时
    两步流程：先 start，再 result
    """
    
    name = "snov"
    display_name = "Snov.io"
    api_type = "api"
    _token = None
    _token_expires = 0
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.client_id = self.config.get('api_user_id')
        self.client_secret = self.config.get('api_key')
        self.base_url = "https://api.snov.io"
    
    def _get_token(self) -> Optional[str]:
        """获取access_token（Snov.io token有效期1小时）"""
        import time
        if SnovSource._token and time.time() < SnovSource._token_expires:
            return SnovSource._token
        
        resp = httpx.post(
            f"{self.base_url}/v1/oauth/access_token",
            data={
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            },
            timeout=30
        )
        
        if resp.status_code == 200:
            data = resp.json()
            SnovSource._token = data.get('access_token')
            SnovSource._token_expires = time.time() + 3500
            return SnovSource._token
        else:
            print(f"[Snov] Token失败: {resp.status_code} {resp.text[:200]}")
            return None
    
    def _headers(self) -> Dict[str, str]:
        token = self._get_token()
        return {'Authorization': f'Bearer {token}'} if token else {}
    
    def search_company(self, domain: str, wait_seconds: int = 3) -> Optional[Dict]:
        """搜索公司信息 - 两步: start -> result
        返回: {company_name, website, hq_phone, industry, city, size}
        """
        if not self.client_id:
            return None
        
        headers = self._headers()
        if not headers:
            return None
        
        # Step1: 发起搜索
        try:
            resp = httpx.post(
                f"{self.base_url}/v2/domain-search/start",
                data={'domain': domain},
                headers=headers,
                timeout=30
            )
            
            if resp.status_code == 202:
                task_hash = resp.json().get('meta', {}).get('task_hash')
            elif resp.status_code == 200:
                # 直接返回结果（已处理完）
                return resp.json().get('data', {})
            else:
                return None
            
            if not task_hash:
                return None
            
            # Step2: 获取结果（异步，需等待）
            import time
            time.sleep(wait_seconds)
            
            resp2 = httpx.get(
                f"{self.base_url}/v2/domain-search/result/{task_hash}",
                headers=headers,
                timeout=30
            )
            
            if resp2.status_code == 200:
                return resp2.json().get('data', {})
        except Exception as e:
            print(f"[Snov] Company search failed: {e}")
        return None
    
    def search(self, keyword: str, country: str = None, 
               limit: int = 100, **kwargs) -> List[BuyerData]:
        """Snov.io不支持产品关键词搜索，跳过"""
        return []
    
    def get_company_details(self, company_id: str) -> Optional[BuyerData]:
        return None
    
    def enrich_buyer(self, buyer: BuyerData) -> BuyerData:
        """补全公司信息 - 通过网站域名"""
        if buyer.website and not buyer.phone:
            domain = buyer.website.replace('https://', '').replace('http://', '').replace('www.', '')
            company_info = self.search_company(domain)
            if company_info:
                buyer.phone = buyer.phone or company_info.get('hq_phone')
                buyer.industry = buyer.industry or company_info.get('industry')
                if company_info.get('city') and not buyer.city:
                    buyer.city = company_info.get('city')
        return buyer
    
    def validate_config(self) -> tuple[bool, str]:
        if not self.client_id:
            return False, "Snov.io API User ID未配置"
        return True, "OK"

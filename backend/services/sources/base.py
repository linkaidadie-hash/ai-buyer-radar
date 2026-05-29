"""
数据源适配器基类
所有数据源需实现此接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class BuyerData:
    """标准化采购商数据格式"""
    company_name: str
    country: str
    city: Optional[str] = None
    industry: Optional[str] = None
    products: List[str] = None
    hs_code: List[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    linkedin: Optional[str] = None
    facebook: Optional[str] = None
    source: str = ""
    source_url: Optional[str] = None
    
    def __post_init__(self):
        if self.products is None:
            self.products = []
        if self.hs_code is None:
            self.hs_code = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'company_name': self.company_name,
            'country': self.country,
            'city': self.city,
            'industry': self.industry,
            'products': self.products,
            'hs_code': self.hs_code,
            'website': self.website,
            'email': self.email,
            'phone': self.phone,
            'whatsapp': self.whatsapp,
            'linkedin': self.linkedin,
            'facebook': self.facebook,
            'source': self.source,
            'source_url': self.source_url,
        }


@dataclass
class ShipmentData:
    """标准化进口记录格式"""
    product: str
    hs_code: Optional[str] = None
    supplier: Optional[str] = None
    origin_country: Optional[str] = None
    quantity: Optional[str] = None
    unit: Optional[str] = None
    date: Optional[str] = None
    value: Optional[str] = None
    source: str = ""
    source_url: Optional[str] = None


class BaseDataSource(ABC):
    """数据源抽象基类"""
    
    name: str = "base"
    display_name: str = "Base Data Source"
    api_type: str = "api"  # api / csv / scraper
    max_per_page: int = 100
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.enabled = config.get('enabled', True) if config else True
    
    @abstractmethod
    def search(self, keyword: str, country: str = None, 
               limit: int = 100, **kwargs) -> List[BuyerData]:
        """
        搜索采购商
        :param keyword: 产品关键词
        :param country: 国家（ISO代码或名称）
        :param limit: 返回数量限制
        :return: 采购商列表
        """
        pass
    
    @abstractmethod
    def get_company_details(self, company_id: str) -> Optional[BuyerData]:
        """获取公司详情"""
        pass
    
    def validate_config(self) -> tuple[bool, str]:
        """验证配置是否正确"""
        return True, "OK"
    
    def transform_to_standard(self, raw_data: Dict[str, Any]) -> BuyerData:
        """
        将数据源原始格式转换为标准格式
        子类可重写
        """
        return BuyerData(
            company_name=raw_data.get('company_name', ''),
            country=raw_data.get('country', ''),
            city=raw_data.get('city'),
            industry=raw_data.get('industry'),
            products=raw_data.get('products', []),
            hs_code=raw_data.get('hs_code', []),
            website=raw_data.get('website'),
            email=raw_data.get('email'),
            phone=raw_data.get('phone'),
            whatsapp=raw_data.get('whatsapp'),
            linkedin=raw_data.get('linkedin'),
            facebook=raw_data.get('facebook'),
            source=self.name,
            source_url=raw_data.get('source_url'),
        )
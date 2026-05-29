"""
Volza 数据源适配器
https://www.volza.com/
进口商数据：采购记录、HS Code、供应商
"""
import re
import json
import httpx
from typing import List, Dict, Any, Optional
from .base import BaseDataSource, BuyerData, ShipmentData


class VolzaSource(BaseDataSource):
    """Volza 进口商数据源"""
    
    name = "volza"
    display_name = "Volza"
    api_type = "csv"  # 第一版用CSV导入
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = self.config.get('api_key')
        self.base_url = self.config.get('base_url', 'https://api.volza.com/v1')
    
    def search(self, keyword: str, country: str = None, 
               limit: int = 100, **kwargs) -> List[BuyerData]:
        """
        Volza CSV导入模式下不支持实时搜索
        返回空列表，实际搜索通过CSV导入实现
        """
        # 如果配置了API，可以使用API搜索
        if self.api_key:
            return self._api_search(keyword, country, limit)
        return []
    
    def _api_search(self, keyword: str, country: str = None, 
                    limit: int = 100) -> List[BuyerData]:
        """通过API搜索（如果Volza提供API）"""
        # Volza目前主要通过CSV导出，API支持待确认
        # 这里预留接口
        return []
    
    def parse_csv_data(self, csv_data: List[Dict[str, Any]]) -> List[BuyerData]:
        """
        解析Volza导出的CSV数据
        Volza典型字段：Company Name, Country, City, Product, HS Code, 
                       Supplier, Origin Country, Quantity, Date, Value
        """
        buyers = []
        seen_companies = {}
        
        for row in csv_data:
            company_name = row.get('Company Name') or row.get('company_name') or ''
            if not company_name:
                continue
            
            # 公司去重（同公司多条记录合并）
            company_key = company_name.lower().strip()
            
            if company_key in seen_companies:
                buyer = seen_companies[company_key]
                # 累加产品
                product = row.get('Product') or row.get('HS Code', '')
                if product and product not in buyer.products:
                    buyer.products.append(product)
            else:
                buyer = BuyerData(
                    company_name=company_name.strip(),
                    country=self._normalize_country(
                        row.get('Country') or row.get('country', '')
                    ),
                    city=row.get('City') or row.get('city', ''),
                    products=[row.get('Product') or row.get('HS Code', '')],
                    hs_code=[row.get('HS Code') or row.get('hs_code', '')],
                    source=self.name,
                    source_url=row.get('url') or row.get('Source URL', ''),
                )
                seen_companies[company_key] = buyer
                buyers.append(buyer)
        
        return buyers
    
    def _normalize_country(self, country: str) -> str:
        """标准化国家名称"""
        # 国家名称映射
        country_map = {
            'UAE': 'United Arab Emirates',
            'U.S.A': 'United States',
            'USA': 'United States',
            'UK': 'United Kingdom',
            'KSA': 'Saudi Arabia',
            'KSA ': 'Saudi Arabia',
        }
        return country_map.get(country.strip(), country.strip())
    
    def get_company_details(self, company_id: str) -> Optional[BuyerData]:
        """获取公司详情（CSV模式不适用）"""
        return None
    
    def transform_shipment_record(self, row: Dict[str, Any]) -> ShipmentData:
        """转换进口记录"""
        return ShipmentData(
            product=row.get('Product', ''),
            hs_code=row.get('HS Code', ''),
            supplier=row.get('Supplier', ''),
            origin_country=row.get('Origin Country', ''),
            quantity=row.get('Quantity', ''),
            unit=row.get('Unit', ''),
            date=row.get('Date', ''),
            value=row.get('Value', ''),
            source=self.name,
        )
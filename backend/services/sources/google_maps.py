"""
Google Maps 数据源适配器
公司信息、电话、网站、Google商家信息
"""
import httpx
from typing import List, Dict, Any, Optional
from .base import BaseDataSource, BuyerData


class GoogleMapsSource(BaseDataSource):
    """Google Maps API 数据源"""
    
    name = "google_maps"
    display_name = "Google Maps API"
    api_type = "api"
    max_per_page = 100
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = self.config.get('api_key')
        self.base_url = "https://maps.googleapis.com/maps/api"
    
    def search(self, keyword: str, country: str = None, 
               limit: int = 100, **kwargs) -> List[BuyerData]:
        """
        通过Google Maps Places API搜索企业
        """
        if not self.api_key:
            return []
        
        results = []
        location = self._get_country_bounds(country) if country else None
        
        # Text Search
        query = f"{keyword} importer" if not country else f"{keyword} importer {country}"
        search_results = self._text_search(query, location, limit)
        
        for place_id in search_results:
            details = self._get_place_details(place_id)
            if details:
                results.append(details)
        
        return results
    
    def _text_search(self, query: str, location: Dict = None, 
                     limit: int = 100) -> List[str]:
        """Google Places Text Search"""
        url = f"{self.base_url}/place/textsearch/json"
        params = {
            'query': query,
            'key': self.api_key,
            'language': 'en',
        }
        if location:
            params['location'] = f"{location['lat']},{location['lng']}"
            params['radius'] = location.get('radius', 50000)
        
        try:
            resp = httpx.get(url, params=params, timeout=30)
            data = resp.json()
            return [r['place_id'] for r in data.get('results', [])[:limit]]
        except Exception as e:
            print(f"[GoogleMaps] Text search failed: {e}")
            return []
    
    def _get_place_details(self, place_id: str) -> Optional[BuyerData]:
        """获取地点详情"""
        url = f"{self.base_url}/place/details/json"
        params = {
            'place_id': place_id,
            'key': self.api_key,
            'fields': 'name,formatted_address,geometry,website,formatted_phone_number',
        }
        
        try:
            resp = httpx.get(url, params=params, timeout=30)
            data = resp.json().get('result', {})
            
            if not data:
                return None
            
            # 判断是否是企业/批发商
            types = data.get('types', [])
            if 'store' not in types and 'wholesale_store' not in types:
                if 'restaurant' in types or 'cafe' in types:
                    return None  # 排除餐饮
            
            address = data.get('formatted_address', '')
            
            return BuyerData(
                company_name=data.get('name', ''),
                country=self._extract_country(address),
                city=self._extract_city(address),
                industry=self._infer_industry(types),
                website=data.get('website'),
                phone=data.get('formatted_phone_number') or 
                      data.get('international_phone_number'),
                source=self.name,
                source_url=f"https://www.google.com/maps/place/{place_id}",
            )
        except Exception as e:
            print(f"[GoogleMaps] Get details failed: {e}")
            return None
    
    def _get_country_bounds(self, country: str) -> Dict:
        """获取国家的中心坐标（简化版）"""
        country_coords = {
            'UAE': {'lat': 25.2048, 'lng': 55.2708, 'radius': 100000},
            'Saudi Arabia': {'lat': 23.8859, 'lng': 45.0792, 'radius': 500000},
            'Nigeria': {'lat': 9.0820, 'lng': 8.6753, 'radius': 200000},
            'Kenya': {'lat': -1.2864, 'lng': 36.8172, 'radius': 100000},
            'Egypt': {'lat': 26.8206, 'lng': 30.8025, 'radius': 200000},
            'India': {'lat': 20.5937, 'lng': 78.9629, 'radius': 500000},
            'Brazil': {'lat': -14.2350, 'lng': -51.9253, 'radius': 500000},
            'Mexico': {'lat': 23.6345, 'lng': -102.5528, 'radius': 500000},
            'Indonesia': {'lat': -0.7893, 'lng': 113.9213, 'radius': 500000},
            'Vietnam': {'lat': 14.0583, 'lng': 108.2772, 'radius': 200000},
            'Pakistan': {'lat': 30.3753, 'lng': 69.3451, 'radius': 200000},
            'Bangladesh': {'lat': 23.6850, 'lng': 90.3563, 'radius': 100000},
        }
        return country_coords.get(country, {'lat': 0, 'lng': 0, 'radius': 500000})
    
    def _extract_country(self, address: str) -> str:
        """从地址提取国家"""
        parts = address.split(',')
        return parts[-1].strip() if parts else address
    
    def _extract_city(self, address: str) -> str:
        """从地址提取城市"""
        parts = address.split(',')
        if len(parts) >= 2:
            return parts[-2].strip()
        return ''
    
    def _infer_industry(self, types: List[str]) -> str:
        """从Google Places类型推断行业"""
        type_map = {
            'wholesale_store': 'Wholesale',
            'furniture_store': 'Furniture',
            'clothing_store': 'Apparel',
            'electronics_store': 'Electronics',
            'building_materials_store': 'Building Materials',
            'hardware_store': 'Hardware',
            'beauty_supply_store': 'Beauty/Cosmetics',
            'sporting_goods_store': 'Sports',
            'jewelry_store': 'Jewelry',
            'toy_store': 'Toys',
        }
        for g_type, industry in type_map.items():
            if g_type in types:
                return industry
        return ''
    
    def get_company_details(self, company_id: str) -> Optional[BuyerData]:
        """获取公司详情"""
        return self._get_place_details(company_id)
    
    def validate_config(self) -> tuple[bool, str]:
        """验证API Key"""
        if not self.api_key:
            return False, "Google Maps API Key未配置"
        return True, "OK"
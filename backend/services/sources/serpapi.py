"""
SerpApi Google Maps 数据源
通过SerpApi代理访问Google Maps数据
覆盖新兴市场（中东/非洲/东南亚）
"""
import httpx
from typing import List, Dict, Any, Optional
from .base import BaseDataSource, BuyerData


# 主要城市坐标映射
CITY_COORDS = {
    # 中东
    'UAE': {'lat': 25.2048, 'lng': 55.2708, 'zoom': 12},
    'Dubai': {'lat': 25.2048, 'lng': 55.2708, 'zoom': 12},
    'Abu Dhabi': {'lat': 24.4539, 'lng': 54.3773, 'zoom': 11},
    'Sharjah': {'lat': 25.3463, 'lng': 55.4209, 'zoom': 12},
    'Saudi Arabia': {'lat': 23.8859, 'lng': 45.0792, 'zoom': 6},
    'Riyadh': {'lat': 24.7136, 'lng': 46.6753, 'zoom': 11},
    'Jeddah': {'lat': 21.4858, 'lng': 39.1925, 'zoom': 11},
    'Kuwait': {'lat': 29.3759, 'lng': 47.9774, 'zoom': 11},
    'Qatar': {'lat': 25.3548, 'lng': 51.1839, 'zoom': 10},
    'Oman': {'lat': 23.5880, 'lng': 58.3829, 'zoom': 10},
    # 非洲
    'Nigeria': {'lat': 9.0820, 'lng': 8.6753, 'zoom': 10},
    'Lagos': {'lat': 6.5244, 'lng': 3.3792, 'zoom': 11},
    'Kenya': {'lat': -1.2864, 'lng': 36.8172, 'zoom': 10},
    'Nairobi': {'lat': -1.2864, 'lng': 36.8172, 'zoom': 12},
    'Egypt': {'lat': 26.8206, 'lng': 30.8025, 'zoom': 10},
    'Cairo': {'lat': 30.0444, 'lng': 31.2357, 'zoom': 11},
    'Ghana': {'lat': 7.9465, 'lng': -1.0232, 'zoom': 10},
    'South Africa': {'lat': -30.5595, 'lng': 22.9375, 'zoom': 6},
    'Johannesburg': {'lat': -26.2041, 'lng': 28.0473, 'zoom': 11},
    'Morocco': {'lat': 31.7917, 'lng': -7.0926, 'zoom': 6},
    'Tanzania': {'lat': -6.3690, 'lng': 34.8888, 'zoom': 6},
    # 东南亚
    'Indonesia': {'lat': -0.7893, 'lng': 113.9213, 'zoom': 6},
    'Vietnam': {'lat': 14.0583, 'lng': 108.2772, 'zoom': 6},
    'Thailand': {'lat': 15.8700, 'lng': 100.9925, 'zoom': 6},
    'Malaysia': {'lat': 4.2105, 'lng': 101.9758, 'zoom': 7},
    'Philippines': {'lat': 12.8797, 'lng': 121.7740, 'zoom': 6},
    'Pakistan': {'lat': 30.3753, 'lng': 69.3451, 'zoom': 7},
    'Bangladesh': {'lat': 23.6850, 'lng': 90.3563, 'zoom': 8},
    'India': {'lat': 20.5937, 'lng': 78.9629, 'zoom': 5},
}


class SerpApiSource(BaseDataSource):
    """SerpApi Google Maps 数据源
    
    通过SerpApi代理访问Google Maps
    优势：覆盖新兴市场（中东/非洲/东南亚）
    数据：公司名/电话/地址/评分/类型
    """
    
    name = "serpapi"
    display_name = "SerpApi Google Maps"
    api_type = "api"
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = self.config.get('api_key')
        self.base_url = "https://serpapi.com"
    
    def search(self, keyword: str, country: str = None, 
               limit: int = 100, **kwargs) -> List[BuyerData]:
        """搜索采购商"""
        if not self.api_key:
            return []
        
        # 确定坐标
        coords = self._get_coords(country or keyword)
        if not coords:
            return []
        
        # ll格式: @lat,lng,zoomz
        ll = f"@{coords['lat']},{coords['lng']},{coords['zoom']}z"
        
        results = []
        fetched = 0
        start = 0
        
        while fetched < limit:
            batch_size = min(20, limit - fetched)
            params = {
                'q': keyword,
                'll': ll,
                'api_key': self.api_key,
                'engine': 'google_maps',
                'limit': batch_size,
                'start': start
            }
            
            try:
                resp = httpx.get(
                    f"{self.base_url}/search.json",
                    params=params,
                    timeout=60
                )
                
                if resp.status_code != 200:
                    break
                
                data = resp.json()
                local_results = data.get('local_results', [])
                
                if not local_results:
                    break
                
                for r in local_results:
                    buyer = self._parse_result(r, keyword, country)
                    if buyer:
                        results.append(buyer)
                    fetched += 1
                    if fetched >= limit:
                        break
                
                start += 20
                
            except Exception as e:
                print(f"[SerpApi] Search failed: {e}")
                break
        
        return results
    
    def _get_coords(self, location: str) -> Optional[Dict]:
        """获取坐标"""
        # 精确匹配
        if location in CITY_COORDS:
            return CITY_COORDS[location]
        
        # 部分匹配
        location_lower = location.lower()
        for key, coords in CITY_COORDS.items():
            if key.lower() in location_lower or location_lower in key.lower():
                return coords
        
        return None
    
    def _parse_result(self, r: Dict, keyword: str, country: str) -> Optional[BuyerData]:
        """解析单个结果"""
        title = r.get('title')
        if not title:
            return None
        
        # 提取电话
        phone = r.get('phone')
        if phone and phone.lower() == 'none':
            phone = None
        
        # 提取地址
        address = r.get('address', '')
        
        # 提取城市
        city = ''
        if address:
            parts = address.split(',')
            if len(parts) >= 2:
                city = parts[-2].strip() if len(parts) >= 3 else parts[-1].strip()
        
        # 评分
        rating = r.get('rating')
        rating_str = str(rating) if rating else None
        
        return BuyerData(
            company_name=title,
            country=country or self._extract_country(address),
            city=city,
            industry=keyword,
            phone=phone,
            website=None,  # Google Maps不提供网站
            source=self.name,
            source_url=r.get('data_id'),
        )
    
    def _extract_country(self, address: str) -> str:
        """从地址提取国家"""
        if not address:
            return ''
        
        country_keywords = {
            'UAE': 'United Arab Emirates', 'Dubai': 'UAE',
            'Saudi': 'Saudi Arabia', 'KSA': 'Saudi Arabia',
            'Nigeria': 'Nigeria', 'Kenya': 'Kenya',
            'Egypt': 'Egypt', 'Ghana': 'Ghana',
            'Indonesia': 'Indonesia', 'Vietnam': 'Vietnam',
            'Malaysia': 'Malaysia', 'Thailand': 'Thailand',
            'Pakistan': 'Pakistan', 'Bangladesh': 'Bangladesh',
            'India': 'India', 'Singapore': 'Singapore',
        }
        
        address_upper = address.upper()
        for keyword, country in country_keywords.items():
            if keyword.upper() in address_upper:
                return country
        
        return ''
    
    def get_company_details(self, company_id: str) -> Optional[BuyerData]:
        """SerpApi不提供详情查询"""
        return None
    
    def validate_config(self) -> tuple[bool, str]:
        if not self.api_key:
            return False, "SerpApi API Key未配置"
        return True, "OK"
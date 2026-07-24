"""
Google Maps 数据源适配器
公司信息、电话、网站、Google商家信息
支持 Text Search + Place Details，含分页、错误处理、国家映射
"""
import httpx
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from .base import BaseDataSource, BuyerData

logger = logging.getLogger(__name__)

# 国家名称标准化映射（支持中文、缩写、全称）
COUNTRY_MAP = {
    # UAE
    'uae': 'United Arab Emirates',
    'united arab emirates': 'United Arab Emirates',
    '阿联酋': 'United Arab Emirates',
    'dubai': 'United Arab Emirates',
    '迪拜': 'United Arab Emirates',
    # Saudi Arabia
    'saudi arabia': 'Saudi Arabia',
    'saudi': 'Saudi Arabia',
    '沙特': 'Saudi Arabia',
    'ksa': 'Saudi Arabia',
    # Vietnam
    'vietnam': 'Vietnam',
    '越南': 'Vietnam',
    # Indonesia
    'indonesia': 'Indonesia',
    '印度尼西亚': 'Indonesia',
    '印尼': 'Indonesia',
    # Kazakhstan
    'kazakhstan': 'Kazakhstan',
    '哈萨克斯坦': 'Kazakhstan',
    # Uzbekistan
    'uzbekistan': 'Uzbekistan',
    '乌兹别克斯坦': 'Uzbekistan',
    # Nigeria
    'nigeria': 'Nigeria',
    '尼日利亚': 'Nigeria',
    # Kenya
    'kenya': 'Kenya',
    '肯尼亚': 'Kenya',
    # Egypt
    'egypt': 'Egypt',
    '埃及': 'Egypt',
    # India
    'india': 'India',
    '印度': 'India',
    # Brazil
    'brazil': 'Brazil',
    '巴西': 'Brazil',
    # Mexico
    'mexico': 'Mexico',
    '墨西哥': 'Mexico',
    # Pakistan
    'pakistan': 'Pakistan',
    '巴基斯坦': 'Pakistan',
    # Bangladesh
    'bangladesh': 'Bangladesh',
    '孟加拉': 'Bangladesh',
    '孟加拉国': 'Bangladesh',
    # Thailand
    'thailand': 'Thailand',
    '泰国': 'Thailand',
    # Malaysia
    'malaysia': 'Malaysia',
    '马来西亚': 'Malaysia',
    # Philippines
    'philippines': 'Philippines',
    '菲律宾': 'Philippines',
    # South Africa
    'south africa': 'South Africa',
    '南非': 'South Africa',
    # Ghana
    'ghana': 'Ghana',
    '加纳': 'Ghana',
    # Tanzania
    'tanzania': 'Tanzania',
    '坦桑尼亚': 'Tanzania',
    # Morocco
    'morocco': 'Morocco',
    '摩洛哥': 'Morocco',
    # Turkey
    'turkey': 'Turkey',
    '土耳其': 'Turkey',
    # Russia
    'russia': 'Russia',
    '俄罗斯': 'Russia',
}

# 国家中心坐标
COUNTRY_COORDS = {
    'United Arab Emirates': {'lat': 25.2048, 'lng': 55.2708, 'radius': 100000},
    'Saudi Arabia': {'lat': 23.8859, 'lng': 45.0792, 'radius': 500000},
    'Vietnam': {'lat': 14.0583, 'lng': 108.2772, 'radius': 200000},
    'Indonesia': {'lat': -0.7893, 'lng': 113.9213, 'radius': 500000},
    'Kazakhstan': {'lat': 48.0196, 'lng': 66.9237, 'radius': 500000},
    'Uzbekistan': {'lat': 41.3775, 'lng': 64.5853, 'radius': 300000},
    'Nigeria': {'lat': 9.0820, 'lng': 8.6753, 'radius': 200000},
    'Kenya': {'lat': -1.2864, 'lng': 36.8172, 'radius': 100000},
    'Egypt': {'lat': 26.8206, 'lng': 30.8025, 'radius': 200000},
    'India': {'lat': 20.5937, 'lng': 78.9629, 'radius': 500000},
    'Brazil': {'lat': -14.2350, 'lng': -51.9253, 'radius': 500000},
    'Mexico': {'lat': 23.6345, 'lng': -102.5528, 'radius': 500000},
    'Pakistan': {'lat': 30.3753, 'lng': 69.3451, 'radius': 200000},
    'Bangladesh': {'lat': 23.6850, 'lng': 90.3563, 'radius': 100000},
    'Thailand': {'lat': 15.8700, 'lng': 100.9925, 'radius': 200000},
    'Malaysia': {'lat': 4.2105, 'lng': 101.9758, 'radius': 200000},
    'Philippines': {'lat': 12.8797, 'lng': 121.7740, 'radius': 200000},
    'South Africa': {'lat': -30.5595, 'lng': 22.9375, 'radius': 500000},
    'Ghana': {'lat': 7.9465, 'lng': -1.0232, 'radius': 100000},
    'Tanzania': {'lat': -6.3690, 'lng': 34.8888, 'radius': 200000},
    'Morocco': {'lat': 31.7917, 'lng': -7.0926, 'radius': 200000},
    'Turkey': {'lat': 38.9637, 'lng': 35.2433, 'radius': 300000},
    'Russia': {'lat': 61.5240, 'lng': 105.3188, 'radius': 500000},
}

# 查询策略后缀
QUERY_SUFFIXES = ['importer', 'wholesaler', 'distributor', 'supplier']

# Place Details 请求字段
DETAILS_FIELDS = (
    'place_id,name,formatted_address,geometry,website,'
    'formatted_phone_number,international_phone_number,'
    'types,business_status,url'
)


class GoogleMapsError(Exception):
    """Google Maps API 错误"""
    def __init__(self, error_code: str, message: str, detail: str = ''):
        self.error_code = error_code
        self.message = message
        self.detail = detail
        super().__init__(message)


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
        self.timeout = self.config.get('timeout', 30)
        self.max_concurrent = self.config.get('max_concurrent', 5)

    def search(self, keyword: str, country: str = None,
               limit: int = 100, **kwargs) -> List[BuyerData]:
        """同步搜索入口（兼容旧调用）"""
        return asyncio.get_event_loop().run_until_complete(
            self.search_async(keyword, country, limit, **kwargs)
        ) if asyncio.get_event_loop().is_running() else self._search_sync(keyword, country, limit, **kwargs)

    def _search_sync(self, keyword: str, country: str = None,
                     limit: int = 100, **kwargs) -> List[BuyerData]:
        """同步搜索实现"""
        if not self.api_key:
            raise GoogleMapsError('API_KEY_MISSING', 'Google Maps API Key 未配置，请前往设置页面配置')

        normalized_country = self._normalize_country(country) if country else None
        queries = self._build_queries(keyword, normalized_country)

        all_place_ids = []
        seen_ids = set()

        for query in queries:
            if len(all_place_ids) >= limit:
                break
            place_ids = self._text_search(query, normalized_country, limit - len(all_place_ids))
            for pid in place_ids:
                if pid not in seen_ids:
                    seen_ids.add(pid)
                    all_place_ids.append(pid)

        results = []
        for place_id in all_place_ids[:limit]:
            details = self._get_place_details(place_id)
            if details:
                results.append(details)

        return results

    async def search_async(self, keyword: str, country: str = None,
                           limit: int = 100, **kwargs) -> List[BuyerData]:
        """异步搜索实现"""
        if not self.api_key:
            raise GoogleMapsError('API_KEY_MISSING', 'Google Maps API Key 未配置，请前往设置页面配置')

        normalized_country = self._normalize_country(country) if country else None
        queries = self._build_queries(keyword, normalized_country)

        all_place_ids = []
        seen_ids = set()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for query in queries:
                if len(all_place_ids) >= limit:
                    break
                place_ids = await self._text_search_async(client, query, normalized_country, limit - len(all_place_ids))
                for pid in place_ids:
                    if pid not in seen_ids:
                        seen_ids.add(pid)
                        all_place_ids.append(pid)

            # 并发获取详情（限制并发数）
            semaphore = asyncio.Semaphore(self.max_concurrent)
            tasks = []
            for place_id in all_place_ids[:limit]:
                tasks.append(self._get_place_details_async(client, place_id, semaphore))

            details_results = await asyncio.gather(*tasks, return_exceptions=True)

        results = []
        for detail in details_results:
            if isinstance(detail, BuyerData):
                results.append(detail)
            elif isinstance(detail, Exception) and not isinstance(detail, GoogleMapsError):
                logger.warning(f"[GoogleMaps] Place details error: {detail}")

        return results

    def _normalize_country(self, country: str) -> Optional[str]:
        """标准化国家名称"""
        if not country:
            return None
        key = country.strip().lower()
        return COUNTRY_MAP.get(key)

    def _build_queries(self, keyword: str, country: str = None) -> List[str]:
        """构建查询策略"""
        keyword_lower = keyword.lower().strip()

        # 如果用户输入已包含商业后缀，不再重复添加
        has_suffix = any(s in keyword_lower for s in QUERY_SUFFIXES)

        queries = []
        if has_suffix:
            # 用户已明确意图，直接用原始关键词
            q = keyword if not country else f"{keyword} {country}"
            queries.append(q)
        else:
            # 多策略查询
            for suffix in QUERY_SUFFIXES:
                if country:
                    q = f"{keyword} {suffix} {country}"
                else:
                    q = f"{keyword} {suffix}"
                queries.append(q)

        return queries

    def _get_location_params(self, country: str) -> Dict[str, str]:
        """获取位置参数，匹配失败时不传location"""
        if not country:
            return {}
        coords = COUNTRY_COORDS.get(country)
        if not coords:
            # 匹配失败：不传location/radius，只在query中包含国家名
            return {}
        return {
            'location': f"{coords['lat']},{coords['lng']}",
            'radius': str(coords.get('radius', 200000)),
        }

    def _text_search(self, query: str, country: str = None,
                     limit: int = 60) -> List[str]:
        """Google Places Text Search（同步，支持分页）"""
        url = f"{self.base_url}/place/textsearch/json"
        params = {
            'query': query,
            'key': self.api_key,
            'language': 'en',
        }
        params.update(self._get_location_params(country))

        place_ids = []
        page_token = None

        try:
            while len(place_ids) < limit:
                if page_token:
                    params['pagetoken'] = page_token
                    # Google 要求等待 token 激活
                    import time
                    time.sleep(2)

                resp = httpx.get(url, params=params, timeout=self.timeout)
                self._check_response(resp)
                data = resp.json()
                self._check_api_status(data)

                results = data.get('results', [])
                for r in results:
                    place_ids.append(r['place_id'])
                    if len(place_ids) >= limit:
                        break

                page_token = data.get('next_page_token')
                if not page_token:
                    break

        except GoogleMapsError:
            raise
        except httpx.TimeoutException:
            raise GoogleMapsError('TIMEOUT', 'Google Places API 请求超时', f'query={query}')
        except Exception as e:
            raise GoogleMapsError('REQUEST_FAILED', f'Google Places API 请求失败: {str(e)}')

        return place_ids

    async def _text_search_async(self, client: httpx.AsyncClient, query: str,
                                 country: str = None, limit: int = 60) -> List[str]:
        """Google Places Text Search（异步，支持分页）"""
        url = f"{self.base_url}/place/textsearch/json"
        params = {
            'query': query,
            'key': self.api_key,
            'language': 'en',
        }
        params.update(self._get_location_params(country))

        place_ids = []
        page_token = None

        try:
            while len(place_ids) < limit:
                if page_token:
                    params['pagetoken'] = page_token
                    await asyncio.sleep(2)

                resp = await client.get(url, params=params)
                self._check_response(resp)
                data = resp.json()
                self._check_api_status(data)

                results = data.get('results', [])
                for r in results:
                    place_ids.append(r['place_id'])
                    if len(place_ids) >= limit:
                        break

                page_token = data.get('next_page_token')
                if not page_token:
                    break

        except GoogleMapsError:
            raise
        except httpx.TimeoutException:
            raise GoogleMapsError('TIMEOUT', 'Google Places API 请求超时', f'query={query}')
        except Exception as e:
            raise GoogleMapsError('REQUEST_FAILED', f'Google Places API 请求失败: {str(e)}')

        return place_ids

    def _check_response(self, resp: httpx.Response):
        """检查HTTP响应状态"""
        if resp.status_code == 403:
            raise GoogleMapsError('API_KEY_INVALID', 'Google Maps API Key 无效或已过期')
        if resp.status_code == 429:
            raise GoogleMapsError('QUOTA_EXCEEDED', 'Google Maps API 配额耗尽，请稍后重试')
        if resp.status_code >= 500:
            raise GoogleMapsError('SERVER_ERROR', f'Google Maps 服务器错误 ({resp.status_code})')
        if resp.status_code != 200:
            raise GoogleMapsError('REQUEST_FAILED', f'Google Maps API 返回异常状态码: {resp.status_code}')

    def _check_api_status(self, data: Dict):
        """检查API返回状态"""
        status = data.get('status', '')
        error_message = data.get('error_message', '')

        if status == 'REQUEST_DENIED':
            detail = error_message or '请求被拒绝'
            if 'API key' in detail.lower() or 'key' in detail.lower():
                raise GoogleMapsError('API_KEY_INVALID', 'Google Maps API Key 无效', detail)
            if 'billing' in detail.lower():
                raise GoogleMapsError('BILLING_NOT_ENABLED', 'Google Maps API 未开启计费', detail)
            if 'not enabled' in detail.lower() or 'disabled' in detail.lower():
                raise GoogleMapsError('API_NOT_ENABLED', 'Google Places API 未启用', detail)
            raise GoogleMapsError('REQUEST_DENIED', 'Google Places API 请求被拒绝', detail)
        elif status == 'OVER_QUERY_LIMIT':
            raise GoogleMapsError('QUOTA_EXCEEDED', 'Google Maps API 配额耗尽', error_message)
        elif status == 'INVALID_REQUEST':
            raise GoogleMapsError('INVALID_REQUEST', 'Google Maps API 请求参数无效', error_message)
        # ZERO_RESULTS 和 OK 都是正常状态，不抛异常

    def _get_place_details(self, place_id: str) -> Optional[BuyerData]:
        """获取地点详情（同步）"""
        url = f"{self.base_url}/place/details/json"
        params = {
            'place_id': place_id,
            'key': self.api_key,
            'fields': DETAILS_FIELDS,
        }

        try:
            resp = httpx.get(url, params=params, timeout=self.timeout)
            if resp.status_code != 200:
                return None
            data = resp.json().get('result', {})
            return self._parse_place_result(data, place_id)
        except GoogleMapsError:
            raise
        except Exception as e:
            logger.warning(f"[GoogleMaps] Get details failed for {place_id}: {e}")
            return None

    async def _get_place_details_async(self, client: httpx.AsyncClient,
                                       place_id: str, semaphore: asyncio.Semaphore) -> Optional[BuyerData]:
        """获取地点详情（异步）"""
        async with semaphore:
            url = f"{self.base_url}/place/details/json"
            params = {
                'place_id': place_id,
                'key': self.api_key,
                'fields': DETAILS_FIELDS,
            }

            try:
                resp = await client.get(url, params=params)
                if resp.status_code != 200:
                    return None
                data = resp.json().get('result', {})
                return self._parse_place_result(data, place_id)
            except Exception as e:
                logger.warning(f"[GoogleMaps] Get details failed for {place_id}: {e}")
                return None

    def _parse_place_result(self, data: Dict, place_id: str) -> Optional[BuyerData]:
        """解析Place Details结果"""
        if not data:
            return None

        types = data.get('types', [])
        # 排除纯餐饮
        if 'restaurant' in types or 'cafe' in types or 'bar' in types:
            if 'wholesale_store' not in types and 'store' not in types:
                return None

        address = data.get('formatted_address', '')

        return BuyerData(
            company_name=data.get('name', ''),
            country=self._extract_country(address),
            city=self._extract_city(address),
            industry=self._infer_industry(types),
            website=data.get('website'),
            phone=data.get('international_phone_number') or data.get('formatted_phone_number'),
            source=self.name,
            source_id=place_id,
            source_url=data.get('url') or f"https://www.google.com/maps/place/?q=place_id:{place_id}",
        )

    def _extract_country(self, address: str) -> str:
        """从地址提取国家"""
        parts = address.split(',')
        return parts[-1].strip() if parts else address

    def _extract_city(self, address: str) -> str:
        """从地址提取城市"""
        parts = address.split(',')
        if len(parts) >= 3:
            return parts[-3].strip()
        elif len(parts) >= 2:
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
            'shoe_store': 'Footwear',
            'home_goods_store': 'Home Goods',
            'department_store': 'Retail',
            'supermarket': 'Food/Grocery',
            'car_dealer': 'Automotive',
        }
        for g_type, industry in type_map.items():
            if g_type in types:
                return industry
        return ''

    def get_company_details(self, company_id: str) -> Optional[BuyerData]:
        """获取公司详情"""
        return self._get_place_details(company_id)

    def validate_config(self) -> tuple:
        """验证API Key"""
        if not self.api_key:
            return False, "Google Maps API Key 未配置，请前往设置页面配置"
        return True, "OK"

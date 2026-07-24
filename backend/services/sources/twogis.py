"""
2GIS 数据源适配器
使用 2GIS Catalog API 搜索商户信息
https://catalog.api.2gis.com/3.0/items
"""
import httpx
from typing import List, Dict, Any, Optional
from .base import BaseDataSource, BuyerData


class TwoGisSource(BaseDataSource):
    """2GIS 商户数据源"""

    name = "2gis"
    display_name = "2GIS"
    api_type = "api"
    max_per_page = 50

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = self.config.get('api_key')
        self.region_id = self.config.get('region_id', '')
        self.base_url = "https://catalog.api.2gis.com/3.0"

    def search(self, keyword: str, country: str = None,
               limit: int = 50, **kwargs) -> List[BuyerData]:
        """
        搜索商户
        :param keyword: 搜索关键词
        :param country: 国家（2GIS主要覆盖俄罗斯及中亚，此参数备用）
        :param limit: 返回数量限制
        """
        if not self.api_key:
            return []

        results = []
        page = 1
        page_size = min(limit, self.max_per_page)

        while len(results) < limit:
            params = {
                'q': keyword,
                'key': self.api_key,
                'page_size': page_size,
                'page': page,
            }
            if self.region_id:
                params['region_id'] = self.region_id

            try:
                resp = httpx.get(
                    f"{self.base_url}/items",
                    params=params,
                    timeout=30
                )
                if resp.status_code != 200:
                    break

                data = resp.json()
                items = data.get('result', {}).get('items', [])
                if not items:
                    break

                for item in items:
                    buyer = self._parse_item(item)
                    if buyer:
                        results.append(buyer)

                total = data.get('result', {}).get('total', 0)
                if page * page_size >= total:
                    break
                page += 1

            except Exception as e:
                print(f"[2GIS] Search failed: {e}")
                break

        return results[:limit]

    def _parse_item(self, item: Dict[str, Any]) -> Optional[BuyerData]:
        """解析2GIS返回的商户数据"""
        name = item.get('name', '')
        if not name:
            return None

        # 地址信息
        address = item.get('address_name', '')
        city = ''
        if address:
            parts = address.split(',')
            if len(parts) >= 2:
                city = parts[-2].strip() if len(parts) > 1 else ''

        # 联系方式
        phone = None
        email = None
        website = None

        contact_groups = item.get('contact_groups', [])
        for group in contact_groups:
            for contact in group.get('contacts', []):
                ctype = contact.get('type', '')
                if ctype == 'phone' and not phone:
                    phone = contact.get('value')
                elif ctype == 'email' and not email:
                    email = contact.get('value')
                elif ctype == 'website' and not website:
                    website = contact.get('url')

        # 外部链接
        external_content = item.get('external_content', [])
        for ext in external_content:
            if ext.get('type') == 'website' and not website:
                website = ext.get('url')

        return BuyerData(
            company_name=name,
            country='RU',  # 2GIS主要覆盖俄罗斯
            city=city,
            industry=item.get('purpose_name'),
            products=[],
            phone=phone,
            email=email,
            website=website,
            source=self.name,
            source_id=str(item.get('id', '')),
        )

    def get_company_details(self, company_id: str) -> Optional[BuyerData]:
        """获取商户详情"""
        if not self.api_key:
            return None

        try:
            resp = httpx.get(
                f"{self.base_url}/items/byid",
                params={'id': company_id, 'key': self.api_key},
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                items = data.get('result', {}).get('items', [])
                if items:
                    return self._parse_item(items[0])
        except Exception as e:
            print(f"[2GIS] Get details failed: {e}")
        return None

    def validate_config(self) -> tuple[bool, str]:
        if not self.api_key:
            return False, "2GIS API Key未配置"
        return True, "OK"

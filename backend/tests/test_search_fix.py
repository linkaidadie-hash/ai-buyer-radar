"""
后端测试 - 覆盖搜索修复的12项核心场景
使用 mock 替代真实外部 API 调用
"""
import sys
import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# 确保 backend 目录在 path 中
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.sources.google_maps import GoogleMapsSource, GoogleMapsError, COUNTRY_MAP
from services.sources.serpapi import SerpApiSource
from services.sources import get_all_sources, create_source
from services.sources.base import BuyerData


# ============================================================
# 1. 未配置 API Key 时返回明确错误
# ============================================================

class TestApiKeyNotConfigured:
    def test_google_maps_no_key(self):
        source = GoogleMapsSource(config={})
        valid, msg = source.validate_config()
        assert not valid
        assert 'API Key' in msg

    def test_google_maps_search_raises(self):
        source = GoogleMapsSource(config={})
        with pytest.raises(GoogleMapsError) as exc_info:
            source._search_sync('jewelry', 'UAE', 10)
        assert exc_info.value.error_code == 'API_KEY_MISSING'

    def test_serpapi_no_key(self):
        source = SerpApiSource(config={})
        valid, msg = source.validate_config()
        assert not valid
        assert 'API Key' in msg


# ============================================================
# 2. 配置可从数据库正确读取
# ============================================================

class TestConfigFromDatabase:
    def test_create_source_with_config(self):
        config = {'api_key': 'test-key-123'}
        source = create_source('google_maps', config)
        assert source is not None
        assert source.api_key == 'test-key-123'

    def test_create_source_serpapi_with_config(self):
        config = {'api_key': 'serp-key-456'}
        source = create_source('serpapi', config)
        assert source is not None
        assert source.api_key == 'serp-key-456'

    @patch('routers.import_data.get_data_source')
    def test_load_source_config(self, mock_get_ds):
        from routers.import_data import _load_source_config
        mock_get_ds.return_value = {
            'name': 'google_maps',
            'config': json.dumps({'api_key': 'db-key-789'})
        }
        config = _load_source_config('google_maps')
        assert config['api_key'] == 'db-key-789'

    @patch('routers.import_data.get_data_source')
    def test_load_source_config_dict(self, mock_get_ds):
        from routers.import_data import _load_source_config
        mock_get_ds.return_value = {
            'name': 'google_maps',
            'config': {'api_key': 'dict-key'}
        }
        config = _load_source_config('google_maps')
        assert config['api_key'] == 'dict-key'


# ============================================================
# 3. Google 返回 REQUEST_DENIED
# ============================================================

class TestRequestDenied:
    def test_request_denied_api_key(self):
        source = GoogleMapsSource(config={'api_key': 'bad-key'})
        data = {
            'status': 'REQUEST_DENIED',
            'error_message': 'The provided API key is invalid.'
        }
        with pytest.raises(GoogleMapsError) as exc_info:
            source._check_api_status(data)
        assert exc_info.value.error_code == 'API_KEY_INVALID'

    def test_request_denied_billing(self):
        source = GoogleMapsSource(config={'api_key': 'key'})
        data = {
            'status': 'REQUEST_DENIED',
            'error_message': 'You must enable Billing on the Google Cloud Project.'
        }
        with pytest.raises(GoogleMapsError) as exc_info:
            source._check_api_status(data)
        assert exc_info.value.error_code == 'BILLING_NOT_ENABLED'

    def test_request_denied_not_enabled(self):
        source = GoogleMapsSource(config={'api_key': 'key'})
        data = {
            'status': 'REQUEST_DENIED',
            'error_message': 'Places API is not enabled for this project.'
        }
        with pytest.raises(GoogleMapsError) as exc_info:
            source._check_api_status(data)
        assert exc_info.value.error_code == 'API_NOT_ENABLED'


# ============================================================
# 4. Google 返回 ZERO_RESULTS
# ============================================================

class TestZeroResults:
    def test_zero_results_no_exception(self):
        source = GoogleMapsSource(config={'api_key': 'key'})
        data = {'status': 'ZERO_RESULTS', 'results': []}
        # 不应抛异常
        source._check_api_status(data)

    @patch('httpx.get')
    def test_text_search_zero_results(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'status': 'ZERO_RESULTS', 'results': []}
        mock_get.return_value = mock_resp

        source = GoogleMapsSource(config={'api_key': 'key'})
        results = source._text_search('nonexistent product xyz', 'UAE', 10)
        assert results == []


# ============================================================
# 5. Google 返回正常商户
# ============================================================

class TestNormalResults:
    @patch('httpx.get')
    def test_text_search_returns_place_ids(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'status': 'OK',
            'results': [
                {'place_id': 'pid_1', 'name': 'Store A'},
                {'place_id': 'pid_2', 'name': 'Store B'},
            ]
        }
        mock_get.return_value = mock_resp

        source = GoogleMapsSource(config={'api_key': 'key'})
        ids = source._text_search('jewelry wholesaler UAE', 'United Arab Emirates', 10)
        assert len(ids) == 2
        assert 'pid_1' in ids

    @patch.object(GoogleMapsSource, '_get_place_details')
    @patch.object(GoogleMapsSource, '_text_search')
    def test_full_search_returns_buyers(self, mock_text_search, mock_details):
        mock_text_search.return_value = ['pid_1']
        mock_details.return_value = BuyerData(
            company_name='Gold Souk Trading',
            country='United Arab Emirates',
            city='Dubai',
            industry='Jewelry',
            website='https://goldsouk.ae',
            phone='+971 4 123 4567',
            source='google_maps',
            source_id='pid_1',
            source_url='https://maps.google.com/?cid=123'
        )

        source = GoogleMapsSource(config={'api_key': 'key'})
        results = source._search_sync('jewelry', 'UAE', 10)
        assert len(results) == 1
        assert results[0].company_name == 'Gold Souk Trading'
        assert results[0].phone == '+971 4 123 4567'
        assert results[0].website == 'https://goldsouk.ae'


# ============================================================
# 6. Place Details 字段正确解析
# ============================================================

class TestPlaceDetailsParsing:
    def test_parse_place_result(self):
        source = GoogleMapsSource(config={'api_key': 'key'})
        data = {
            'name': 'Test Company LLC',
            'formatted_address': '123 Main St, Dubai, United Arab Emirates',
            'geometry': {'location': {'lat': 25.2, 'lng': 55.3}},
            'website': 'https://testco.com',
            'international_phone_number': '+971 50 111 2222',
            'formatted_phone_number': '050 111 2222',
            'types': ['wholesale_store', 'electronics_store'],
            'business_status': 'OPERATIONAL',
            'url': 'https://maps.google.com/place/test'
        }
        buyer = source._parse_place_result(data, 'test_place_id')
        assert buyer is not None
        assert buyer.company_name == 'Test Company LLC'
        assert buyer.country == 'United Arab Emirates'
        assert buyer.phone == '+971 50 111 2222'
        assert buyer.website == 'https://testco.com'
        assert buyer.source_id == 'test_place_id'
        assert buyer.industry == 'Wholesale'  # wholesale_store matched first

    def test_parse_restaurant_excluded(self):
        source = GoogleMapsSource(config={'api_key': 'key'})
        data = {
            'name': 'Pizza Place',
            'formatted_address': '456 Food St, Dubai, UAE',
            'types': ['restaurant', 'food'],
        }
        buyer = source._parse_place_result(data, 'pid')
        assert buyer is None


# ============================================================
# 7. 重复商户不会重复插入
# ============================================================

class TestDeduplication:
    def test_dedup_by_source_id(self):
        from routers.import_data import _deduplicate_buyers
        conn = MagicMock()
        # 模拟 source_id 已存在
        cursor = MagicMock()
        cursor.fetchone.return_value = {'id': 1}
        conn.execute.return_value = cursor

        buyers = [{
            'company_name': 'Existing Co',
            'source': 'google_maps',
            'source_id': 'pid_existing',
            'source_url': 'https://maps.google.com/?q=place_id:pid_existing',
            'country': 'UAE',
            'city': 'Dubai',
        }]
        new_buyers, dups = _deduplicate_buyers(conn, buyers)
        assert dups == 1
        assert len(new_buyers) == 0

    def test_dedup_by_company_country_city(self):
        from routers.import_data import _deduplicate_buyers
        conn = MagicMock()

        call_count = [0]
        def mock_execute(sql, params=None):
            call_count[0] += 1
            cursor = MagicMock()
            # source_id check: no match
            if 'source_url' in sql:
                cursor.fetchone.return_value = None
            # website check: no match
            elif 'website' in sql:
                cursor.fetchone.return_value = None
            # company+country+city: match!
            elif 'company_name' in sql:
                cursor.fetchone.return_value = {'id': 1}
            else:
                cursor.fetchone.return_value = None
            return cursor

        conn.execute.side_effect = mock_execute

        buyers = [{
            'company_name': 'Same Company',
            'source': 'google_maps',
            'source_id': None,
            'website': None,
            'phone': None,
            'country': 'UAE',
            'city': 'Dubai',
        }]
        new_buyers, dups = _deduplicate_buyers(conn, buyers)
        assert dups == 1
        assert len(new_buyers) == 0


# ============================================================
# 8. 中文国家名称能标准化
# ============================================================

class TestCountryNormalization:
    def test_chinese_uae(self):
        source = GoogleMapsSource(config={'api_key': 'key'})
        assert source._normalize_country('阿联酋') == 'United Arab Emirates'

    def test_chinese_saudi(self):
        source = GoogleMapsSource(config={'api_key': 'key'})
        assert source._normalize_country('沙特') == 'Saudi Arabia'

    def test_chinese_vietnam(self):
        source = GoogleMapsSource(config={'api_key': 'key'})
        assert source._normalize_country('越南') == 'Vietnam'

    def test_chinese_indonesia(self):
        source = GoogleMapsSource(config={'api_key': 'key'})
        assert source._normalize_country('印度尼西亚') == 'Indonesia'

    def test_chinese_kazakhstan(self):
        source = GoogleMapsSource(config={'api_key': 'key'})
        assert source._normalize_country('哈萨克斯坦') == 'Kazakhstan'

    def test_chinese_uzbekistan(self):
        source = GoogleMapsSource(config={'api_key': 'key'})
        assert source._normalize_country('乌兹别克斯坦') == 'Uzbekistan'

    def test_english_uae(self):
        source = GoogleMapsSource(config={'api_key': 'key'})
        assert source._normalize_country('UAE') == 'United Arab Emirates'
        assert source._normalize_country('United Arab Emirates') == 'United Arab Emirates'

    def test_english_saudi(self):
        source = GoogleMapsSource(config={'api_key': 'key'})
        assert source._normalize_country('Saudi Arabia') == 'Saudi Arabia'
        assert source._normalize_country('Saudi') == 'Saudi Arabia'


# ============================================================
# 9. 未识别国家不会落到 0,0
# ============================================================

class TestUnknownCountry:
    def test_unknown_country_no_location(self):
        source = GoogleMapsSource(config={'api_key': 'key'})
        params = source._get_location_params('Atlantis')
        assert params == {}

    def test_unknown_country_not_zero_zero(self):
        source = GoogleMapsSource(config={'api_key': 'key'})
        params = source._get_location_params('Unknown Land')
        # 不应返回 lat=0, lng=0
        assert 'location' not in params

    def test_known_country_has_location(self):
        source = GoogleMapsSource(config={'api_key': 'key'})
        params = source._get_location_params('United Arab Emirates')
        assert 'location' in params
        assert '25.2048' in params['location']


# ============================================================
# 10. 外部请求超时
# ============================================================

class TestTimeout:
    @patch('httpx.get')
    def test_timeout_raises_error(self, mock_get):
        import httpx
        mock_get.side_effect = httpx.TimeoutException('Connection timed out')

        source = GoogleMapsSource(config={'api_key': 'key'})
        with pytest.raises(GoogleMapsError) as exc_info:
            source._text_search('test query', 'UAE', 10)
        assert exc_info.value.error_code == 'TIMEOUT'


# ============================================================
# 11. 搜索已保存商户仍正常
# ============================================================

class TestLocalSearch:
    def test_advanced_search_endpoint_exists(self):
        """验证本地搜索路由仍然存在"""
        from routers.search import router
        routes = [r.path for r in router.routes]
        assert '/advanced' in routes

    def test_quick_search_endpoint_exists(self):
        from routers.search import router
        routes = [r.path for r in router.routes]
        assert '/quick' in routes


# ============================================================
# 12. SerpAPI 注册状态正确
# ============================================================

class TestSerpApiRegistration:
    def test_serpapi_in_registry(self):
        sources = get_all_sources()
        assert 'serpapi' in sources

    def test_serpapi_create_instance(self):
        source = create_source('serpapi', {'api_key': 'test'})
        assert source is not None
        assert source.name == 'serpapi'

    def test_snov_in_registry(self):
        sources = get_all_sources()
        assert 'snov' in sources

    def test_google_maps_in_registry(self):
        sources = get_all_sources()
        assert 'google_maps' in sources

    def test_all_search_sources_registered(self):
        sources = get_all_sources()
        for name in ['google_maps', 'serpapi', 'zoominfo', 'apollo']:
            assert name in sources, f'{name} not registered'


# ============================================================
# 额外：查询策略测试
# ============================================================

class TestQueryStrategy:
    def test_no_duplicate_suffix(self):
        source = GoogleMapsSource(config={'api_key': 'key'})
        queries = source._build_queries('jewelry wholesalers', 'United Arab Emirates')
        # 用户已包含 wholesaler，不应再添加
        assert len(queries) == 1
        assert 'jewelry wholesalers United Arab Emirates' in queries[0]

    def test_adds_suffixes(self):
        source = GoogleMapsSource(config={'api_key': 'key'})
        queries = source._build_queries('jewelry', 'United Arab Emirates')
        assert len(queries) == 4
        assert any('importer' in q for q in queries)
        assert any('wholesaler' in q for q in queries)
        assert any('distributor' in q for q in queries)
        assert any('supplier' in q for q in queries)

    def test_no_country(self):
        source = GoogleMapsSource(config={'api_key': 'key'})
        queries = source._build_queries('rubber necklace', None)
        assert len(queries) == 4
        assert all('rubber necklace' in q for q in queries)

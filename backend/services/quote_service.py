"""
外贸报价服务
产品库 + AI报价 + 运费计算 + 报价单生成
"""
import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path


class ProductService:
    """产品库管理"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "database" / "buyers.db"
            db_path = str(db_path)
        self.db_path = db_path
    
    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def list_products(self, category: str = None, status: str = 'active') -> List[Dict]:
        """产品列表"""
        with self.get_conn() as conn:
            sql = "SELECT * FROM products WHERE status = ?"
            params = [status]
            if category:
                sql += " AND category = ?"
                params.append(category)
            sql += " ORDER BY id"
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]
    
    def get_product(self, product_id: int) -> Optional[Dict]:
        """获取产品"""
        with self.get_conn() as conn:
            row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            return dict(row) if row else None
    
    def add_product(self, data: Dict) -> int:
        """添加产品"""
        with self.get_conn() as conn:
            # 计算体积
            volume = 0
            if data.get('length_cm') and data.get('width_cm') and data.get('height_cm'):
                volume = data['length_cm'] * data['width_cm'] * data['height_cm'] / 1_000_000
            
            cursor = conn.execute("""
                INSERT INTO products (name_cn, name_en, sku, cost_price, moq, unit,
                    length_cm, width_cm, height_cm, weight_kg, volume_m3, profit_rate, category, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('name_cn'),
                data.get('name_en'),
                data.get('sku'),
                data.get('cost_price', 0),
                data.get('moq', 100),
                data.get('unit', 'pcs'),
                data.get('length_cm', 0),
                data.get('width_cm', 0),
                data.get('height_cm', 0),
                data.get('weight_kg', 0),
                volume,
                data.get('profit_rate', 30),
                data.get('category'),
                data.get('description')
            ))
            conn.commit()
            return cursor.lastrowid


class QuoteService:
    """AI报价服务"""
    
    # 港口杂费 (USD)
    PORT_FEES = {
        'Shanghai': 150,
        'Ningbo': 120,
        'Shenzhen': 130,
    }
    
    # 保险费率 (CIF的%)
    INSURANCE_RATE = 0.01
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "database" / "buyers.db"
            db_path = str(db_path)
        self.db_path = db_path
    
    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_shipping_rate(self, country: str, method: str = 'sea') -> Optional[Dict]:
        """获取运费"""
        with self.get_conn() as conn:
            row = conn.execute("""
                SELECT * FROM shipping_rates 
                WHERE country = ? AND shipping_method = ?
            """, (country, method)).fetchone()
            return dict(row) if row else None
    
    def calculate_quote(self, items: List[Dict], country: str,
                       shipping_method: str = 'sea',
                       price_term: str = 'FOB Shanghai',
                       port_from: str = 'Shanghai') -> Dict:
        """
        计算报价
        items: [{product_id, quantity, unit_price(可选)}]
        """
        with self.get_conn() as conn:
            # 计算产品明细
            product_items = []
            total_fob = 0
            total_cost = 0
            
            for item in items:
                product = conn.execute(
                    "SELECT * FROM products WHERE id = ?", (item['product_id'],)
                ).fetchone()
                
                if not product:
                    continue
                
                product = dict(product)
                qty = item.get('quantity', 1)
                
                # 计算价格
                cost = product['cost_price']
                profit_rate = product.get('profit_rate', 30) / 100
                
                # 有自定义单价用自定义的，否则按成本+利润
                if item.get('unit_price'):
                    fob_price = item['unit_price']
                else:
                    fob_price = cost * (1 + profit_rate) * 7.2  # CNY to USD (假设汇率7.2)
                
                # 小计
                fob_subtotal = fob_price * qty
                cost_subtotal = cost * qty
                
                product_items.append({
                    'product_id': product['id'],
                    'name': product['name_en'] or product['name_cn'],
                    'sku': product['sku'],
                    'quantity': qty,
                    'unit': product['unit'],
                    'cost_price': cost,
                    'fob_price': round(fob_price, 2),
                    'fob_subtotal': round(fob_subtotal, 2),
                })
                
                total_fob += fob_subtotal
                total_cost += cost_subtotal
            
            # 计算运费
            shipping_rate = self.get_shipping_rate(country, shipping_method)
            
            if shipping_rate:
                # 计算总体积和总重量
                total_volume = 0
                total_weight = 0
                
                for item in items:
                    product = conn.execute(
                        "SELECT * FROM products WHERE id = ?", (item['product_id'],)
                    ).fetchone()
                    if product:
                        product = dict(product)
                        qty = item.get('quantity', 1)
                        total_volume += (product['length_cm'] * product['width_cm'] * product['height_cm'] / 1_000_000) * qty
                        total_weight += product['weight_kg'] * qty
                
                # 按体积计费 vs 按重量计费，取较大者
                volume_cost = shipping_rate['rate_per_m3'] * total_volume
                weight_cost = shipping_rate['rate_per_kg'] * total_weight
                shipping_cost = max(volume_cost, shipping_rate['min_charge'])
                shipping_cost = max(shipping_cost, weight_cost)
            else:
                shipping_cost = 0
                total_volume = 0
                total_weight = 0
            
            # 港口杂费
            port_fee = self.PORT_FEES.get(port_from, 150)
            
            # CIF计算
            cif_value = total_fob + shipping_cost + port_fee
            insurance = cif_value * self.INSURANCE_RATE
            cif_price = cif_value + insurance
            
            # 利润
            profit = total_fob - (total_cost * 7.2)  # FOB收入 - 成本
            profit_rate = (profit / (total_cost * 7.2) * 100) if total_cost > 0 else 0
            
            return {
                'items': product_items,
                'summary': {
                    'total_quantity': sum(i['quantity'] for i in product_items),
                    'total_fob': round(total_fob, 2),
                    'total_cost_cny': round(total_cost, 2),
                    'profit_cny': round(profit, 2),
                    'profit_rate': round(profit_rate, 1),
                },
                'logistics': {
                    'port_from': port_from,
                    'port_to': country,
                    'shipping_method': shipping_method,
                    'shipping_cost': round(shipping_cost, 2),
                    'port_fee': port_fee,
                    'total_volume_m3': round(total_volume, 4),
                    'total_weight_kg': round(total_weight, 2),
                },
                'cif': {
                    'fob_value': round(total_fob, 2),
                    'shipping': round(shipping_cost, 2),
                    'port_fee': port_fee,
                    'insurance': round(insurance, 2),
                    'cif_value': round(cif_price, 2),
                },
                'price_terms': {
                    'fob_shanghai': round(total_fob, 2),
                    'cif': round(cif_price, 2),
                }
            }
    
    def create_quotation(self, buyer: Dict, items: List[Dict], country: str,
                        shipping_method: str = 'sea') -> Dict:
        """创建报价单"""
        with self.get_conn() as conn:
            # 生成报价单号
            today = datetime.now()
            date_str = today.strftime('%Y%m%d')
            
            # 查询今天的序号
            prefix = f"Q-{date_str}-"
            last_no = conn.execute("""
                SELECT quotation_no FROM quotations 
                WHERE quotation_no LIKE ? 
                ORDER BY quotation_no DESC LIMIT 1
            """, (f"{prefix}%",)).fetchone()
            
            if last_no:
                seq = int(last_no[0].split('-')[-1]) + 1
            else:
                seq = 1
            
            quotation_no = f"{prefix}{seq:03d}"
            
            # 计算报价
            quote = self.calculate_quote(items, country, shipping_method)
            
            # 有效期14天
            valid_until = (today + timedelta(days=14)).strftime('%Y-%m-%d')
            
            cursor = conn.execute("""
                INSERT INTO quotations (
                    quotation_no, buyer_name, buyer_country, buyer_phone, buyer_email,
                    items, total_amount, price_term, shipping_method, port_to,
                    valid_until, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft')
            """, (
                quotation_no,
                buyer.get('name'),
                buyer.get('country'),
                buyer.get('phone'),
                buyer.get('email'),
                json.dumps(items, ensure_ascii=False),
                quote['summary']['total_fob'],
                'FOB Shanghai',
                shipping_method,
                country,
                valid_until
            ))
            conn.commit()
            quotation_id = cursor.lastrowid
            
            return {
                'id': quotation_id,
                'quotation_no': quotation_no,
                'quote': quote,
                'valid_until': valid_until
            }
    
    def get_quotation(self, quotation_id: int) -> Optional[Dict]:
        """获取报价单"""
        with self.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM quotations WHERE id = ?", (quotation_id,)
            ).fetchone()
            if not row:
                return None
            
            result = dict(row)
            result['items'] = json.loads(result['items'])
            return result


class OrderService:
    """订单服务"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "database" / "buyers.db"
            db_path = str(db_path)
        self.db_path = db_path
    
    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_order(self, quotation_id: int, buyer: Dict, items: List[Dict],
                    total_amount: float) -> Dict:
        """创建订单"""
        with self.get_conn() as conn:
            today = datetime.now()
            date_str = today.strftime('%Y%m%d')
            
            prefix = f"OR-{date_str}-"
            last_no = conn.execute("""
                SELECT order_no FROM orders 
                WHERE order_no LIKE ? 
                ORDER BY order_no DESC LIMIT 1
            """, (f"{prefix}%",)).fetchone()
            
            if last_no:
                seq = int(last_no[0].split('-')[-1]) + 1
            else:
                seq = 1
            
            order_no = f"{prefix}{seq:03d}"
            
            cursor = conn.execute("""
                INSERT INTO orders (
                    order_no, quotation_id, buyer_name, buyer_country,
                    items, total_amount, status, inquiry_date
                ) VALUES (?, ?, ?, ?, ?, ?, 'inquiry', ?)
            """, (
                order_no,
                quotation_id,
                buyer.get('name'),
                buyer.get('country'),
                json.dumps(items, ensure_ascii=False),
                total_amount,
                today.strftime('%Y-%m-%d')
            ))
            conn.commit()
            
            return {
                'id': cursor.lastrowid,
                'order_no': order_no
            }
    
    def update_status(self, order_id: int, status: str) -> bool:
        """更新订单状态"""
        with self.get_conn() as conn:
            today = datetime.now().strftime('%Y-%m-%d')
            
            status_field = {
                'quote': 'quote_date',
                'sample': 'sample_date',
                'payment': 'payment_date',
                'production': 'production_date',
                'shipped': 'shipment_date',
                'delivered': 'delivery_date',
            }.get(status)
            
            sql = f"UPDATE orders SET status = ?, updated_at = ?"
            params = [status, today]
            
            if status_field:
                sql += f", {status_field} = ?"
                params.append(today)
            
            sql += " WHERE id = ?"
            params.append(order_id)
            
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor.rowcount > 0
    
    def get_order(self, order_id: int) -> Optional[Dict]:
        """获取订单"""
        with self.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM orders WHERE id = ?", (order_id,)
            ).fetchone()
            if not row:
                return None
            
            result = dict(row)
            result['items'] = json.loads(result['items'])
            return result
    
    def list_orders(self, status: str = None, limit: int = 50) -> List[Dict]:
        """订单列表"""
        with self.get_conn() as conn:
            sql = "SELECT * FROM orders"
            params = []
            if status:
                sql += " WHERE status = ?"
                params.append(status)
            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            rows = conn.execute(sql, params).fetchall()
            result = []
            for row in rows:
                r = dict(row)
                r['items'] = json.loads(r['items'])
                result.append(r)
            return result


class ShippingService:
    """运费查询"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "database" / "buyers.db"
            db_path = str(db_path)
        self.db_path = db_path
    
    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def list_rates(self, country: str = None) -> List[Dict]:
        """运费列表"""
        with self.get_conn() as conn:
            if country:
                rows = conn.execute("""
                    SELECT * FROM shipping_rates WHERE country = ?
                """, (country,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM shipping_rates ORDER BY country
                """).fetchall()
            return [dict(row) for row in rows]
    
    def get_quote(self, country: str, method: str, volume_m3: float, 
                  weight_kg: float) -> Dict:
        """计算运费"""
        rate = self.get_shipping_rate(country, method)
        if not rate:
            return {'error': f'No shipping rate for {country}'}
        
        volume_cost = rate['rate_per_m3'] * volume_m3
        weight_cost = rate['rate_per_kg'] * weight_kg
        total = max(volume_cost, weight_cost, rate['min_charge'])
        
        return {
            'country': country,
            'method': method,
            'volume_cost': round(volume_cost, 2),
            'weight_cost': round(weight_cost, 2),
            'total': round(total, 2),
            'min_charge': rate['min_charge'],
            'transit_days': rate.get('transit_days', 'TBD'),
        }
    
    def get_shipping_rate(self, country: str, method: str = 'sea') -> Optional[Dict]:
        """获取单个国家运费"""
        with self.get_conn() as conn:
            row = conn.execute("""
                SELECT * FROM shipping_rates 
                WHERE country = ? AND shipping_method = ?
            """, (country, method)).fetchone()
            return dict(row) if row else None
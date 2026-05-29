#!/usr/bin/env python3
"""
AI Buyer Radar - Windows 桌面应用入口
系统托盘 + API服务 + Web界面
"""
import sys
import os
import json
import threading
import webbrowser
import logging
from pathlib import Path
from datetime import datetime

# 确保路径正确
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / 'backend'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / 'logs' / 'app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 配置文件
CONFIG_FILE = BASE_DIR / 'config.json'
DB_PATH = BASE_DIR / 'database' / 'buyers.db'
PORT = 8001


def load_config():
    """加载配置"""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
    return {
        'api_port': PORT,
        'auto_start': False,
        'minimize_to_tray': True,
        'open_browser': True
    }


def save_config(config):
    """保存配置"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding='utf-8')


def init_database():
    """初始化数据库"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # 初始化数据库
    from services.database import init_db
    init_db()
    logger.info(f'数据库已就绪: {DB_PATH}')


def start_api_server():
    """启动API服务器"""
    import uvicorn
    from backend.main import app
    
    config = uvicorn.Config(
        app,
        host='127.0.0.1',
        port=PORT,
        log_level='info'
    )
    server = uvicorn.Server(config)
    
    logger.info(f'API服务启动: http://localhost:{PORT}')
    logger.info(f'API文档: http://localhost:{PORT}/docs')
    
    # 在独立线程中运行
    thread = threading.Thread(target=lambda: server.run(), daemon=True)
    thread.start()
    return thread


def open_browser():
    """打开浏览器"""
    import time
    time.sleep(2)
    webbrowser.open(f'http://localhost:{PORT}/')


def create_system_tray():
    """创建系统托盘 (Windows)"""
    try:
        import pystray
        from PIL import Image, ImageDraw
        
        # 创建图标图像
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), '#667eea')
        draw = ImageDraw.Draw(image)
        draw.ellipse([8, 8, 56, 56], fill='#fff', outline='#764ba2', width=3)
        draw.text((20, 22), 'AI', fill='#667eea')
        
        def on_click(icon, item):
            if str(item) == '打开主界面':
                webbrowser.open(f'http://localhost:{PORT}')
            elif str(item) == '快速报价':
                webbrowser.open(f'http://localhost:{PORT}/quote')
            elif str(item) == 'API状态':
                logger.info(f'API服务运行中: http://localhost:{PORT}')
            elif str(item) == '退出':
                icon.stop()
                sys.exit(0)
        
        menu = pystray.Menu(
            pystray.MenuItem('打开主界面', on_click),
            pystray.MenuItem('快速报价', on_click),
            pystray.MenuItem('API状态', on_click),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('退出', on_click),
        )
        
        icon = pystray.Icon('AI-Buyer-Radar', image, 'AI Buyer Radar', menu)
        icon.run()
    except ImportError:
        logger.warning('pystray未安装，托盘功能不可用')


def main():
    """主函数"""
    logger.info('=' * 50)
    logger.info('AI Buyer Radar 启动中...')
    logger.info('=' * 50)
    
    # 创建logs目录
    (BASE_DIR / 'logs').mkdir(parents=True, exist_ok=True)
    
    # 加载配置
    config = load_config()
    
    # 初始化数据库
    init_database()
    
    # 启动API服务
    api_thread = start_api_server()
    
    # 打开浏览器
    if config.get('open_browser', True):
        open_browser()
    
    logger.info('AI Buyer Radar 运行中...')
    logger.info(f'按 Ctrl+C 停止服务')
    
    # 尝试启动系统托盘
    try:
        create_system_tray()
    except Exception as e:
        logger.warning(f'托盘启动失败: {e}')
        logger.info('服务持续运行中...')
        
        # 保持运行
        try:
            api_thread.join()
        except KeyboardInterrupt:
            logger.info('服务已停止')
            sys.exit(0)


if __name__ == '__main__':
    main()
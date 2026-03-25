#!/usr/bin/env python3
"""
使用键盘导航的发布脚本
"""

import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from loguru import logger

def publish_with_keyboard():
    """使用键盘操作发布"""
    
    cookie_file = Path("cookies/xhs_cookies.json")
    content_file = Path("output/contract_xhs/xhs_content.json")
    
    with open(content_file, 'r', encoding='utf-8') as f:
        content_data = json.load(f)
    
    image_paths = [Path(p) for p in content_data['images']]
    title = content_data['title']
    content = content_data['content']
    tags = content_data['tags']
    
    full_content = content + "\n\n" + " ".join([f"#{tag}" for tag in tags])
    
    logger.info("🚀 使用键盘导航发布")
    logger.info(f"标题: {title}")
    logger.info(f"图片: {len(image_paths)} 张")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        context = browser.new_context(
            storage_state=str(cookie_file),
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        try:
            # 访问页面
            logger.info("📄 步骤1: 访问页面...")
            page.goto("https://creator.xiaohongshu.com/publish/publish",
                     wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)
            page.screenshot(path="output/keyboard/01_loaded.png")
            
            # 尝试使用键盘切换标签
            logger.info("📄 步骤2: 使用键盘切换到上传图文...")
            logger.info("  按Tab键定位到标签...")
            page.keyboard.press("Tab")
            time.sleep(0.5)
            page.keyboard.press("Tab")
            time.sleep(0.5)
            
            # 按右箭头键切换到第二个标签
            logger.info("  按右箭头键切换标签...")
            page.keyboard.press("ArrowRight")
            time.sleep(1)
            page.screenshot(path="output/keyboard/02_after_arrow.png")
            
            # 按回车选中
            logger.info("  按回车确认选择...")
            page.keyboard.press("Enter")
            time.sleep(3)
            page.screenshot(path="output/keyboard/03_after_enter.png")
            
            # 检查是否切换成功
            file_inputs = page.query_selector_all('input[type="file"]')
            if file_inputs:
                accept = file_inputs[0].get_attribute("accept") or ""
                logger.info(f"  文件输入accept: {accept}")
                if "image" in accept.lower() or ".jpg" in accept:
                    logger.success("✅ 成功切换到图文模式！")
                else:
                    logger.warning("⚠️ 仍然是视频模式")
            
            # 保持打开观察
            logger.info("⏳ 保持浏览器打开60秒观察...")
            time.sleep(60)
            
        except Exception as e:
            logger.error(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            page.screenshot(path="output/keyboard/error.png")
            time.sleep(30)
        finally:
            browser.close()

if __name__ == "__main__":
    Path("output/keyboard").mkdir(parents=True, exist_ok=True)
    publish_with_keyboard()

#!/usr/bin/env python3
"""
分析小红书发布页面结构
"""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from loguru import logger

def analyze_page_structure():
    """分析小红书发布页面结构"""
    
    cookie_file = Path("cookies/xhs_cookies.json")
    if not cookie_file.exists():
        logger.error("❌ Cookie文件不存在，请先运行 python main.py login")
        return
    
    logger.info("🚀 启动浏览器分析页面...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # 非headless方便观察
        context = browser.new_context(storage_state=str(cookie_file))
        page = context.new_page()
        
        try:
            # 访问创作者中心首页
            logger.info("📄 访问创作者中心...")
            page.goto("https://creator.xiaohongshu.com/", timeout=60000)
            time.sleep(3)
            
            page.screenshot(path="output/xhs_analysis/step1_home.png")
            logger.success("📷 首页截图: output/xhs_analysis/step1_home.png")
            
            # 查找并点击"发布笔记"按钮
            logger.info("🔍 查找发布笔记按钮...")
            
            # 尝试多个可能的选择器
            publish_selectors = [
                "button:has-text('发布笔记')",
                "a:has-text('发布笔记')",
                ".publish-btn",
                "[data-v-7cbccdb2-s]:has-text('发布')",
            ]
            
            publish_button = None
            for selector in publish_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        publish_button = element
                        logger.success(f"✅ 找到发布按钮: {selector}")
                        break
                except:
                    continue
            
            if not publish_button:
                # 尝试获取所有包含"发布"文本的元素
                logger.info("🔍 搜索所有包含'发布'的元素...")
                page.screenshot(path="output/xhs_analysis/step2_looking_for_publish.png")
                
                # 打印页面上所有按钮和链接
                all_buttons = page.query_selector_all("button")
                logger.info(f"📋 页面上有 {len(all_buttons)} 个按钮")
                
                for i, btn in enumerate(all_buttons[:10]):  # 只看前10个
                    text = btn.text_content()
                    if text and "发布" in text:
                        logger.info(f"  按钮 {i}: {text}")
                        publish_button = btn
                        break
            
            if publish_button:
                logger.info("👆 点击发布笔记按钮...")
                publish_button.click()
                time.sleep(3)
                
                page.screenshot(path="output/xhs_analysis/step3_after_click_publish.png")
                logger.success("📷 点击后截图: output/xhs_analysis/step3_after_click_publish.png")
            
            # 直接访问发布页面
            logger.info("📄 直接访问图文发布页面...")
            page.goto("https://creator.xiaohongshu.com/publish/publish?source=official", 
                     wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)
            
            page.screenshot(path="output/xhs_analysis/step4_publish_page.png")
            logger.success("📷 发布页面截图: output/xhs_analysis/step4_publish_page.png")
            
            # 分析页面元素
            logger.info("🔍 分析页面元素...")
            
            # 查找上传区域
            logger.info("\n1️⃣ 查找图片上传区域...")
            upload_area = page.query_selector(".upload-input, input[type='file']")
            if upload_area:
                logger.success(f"  ✅ 找到上传区域")
            
            # 查找标题输入框
            logger.info("\n2️⃣ 查找标题输入框...")
            title_selectors = [
                "input[placeholder*='标题']",
                "input[placeholder*='填写标题']",
                ".title-input input",
                "#post-textarea",
                "[contenteditable='true']",
            ]
            
            for selector in title_selectors:
                elements = page.query_selector_all(selector)
                if elements:
                    logger.info(f"  找到 {len(elements)} 个元素: {selector}")
                    for i, elem in enumerate(elements):
                        placeholder = elem.get_attribute("placeholder") or ""
                        logger.info(f"    [{i}] placeholder: {placeholder}")
            
            # 查找内容输入框
            logger.info("\n3️⃣ 查找内容输入框...")
            content_selectors = [
                "textarea",
                "[contenteditable='true']",
                "#post-textarea",
                ".content-input",
            ]
            
            for selector in content_selectors:
                elements = page.query_selector_all(selector)
                if elements:
                    logger.info(f"  找到 {len(elements)} 个元素: {selector}")
            
            # 保存页面HTML
            html_content = page.content()
            html_file = Path("output/xhs_analysis/page_source.html")
            html_file.parent.mkdir(parents=True, exist_ok=True)
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.success(f"💾 页面源码已保存: {html_file}")
            
            # 等待用户观察
            logger.info("\n⏸️  浏览器将保持打开状态60秒，请观察页面...")
            logger.info("   您可以手动操作页面，查看元素结构")
            time.sleep(60)
            
            browser.close()
            logger.success("✅ 分析完成！")
            
        except Exception as e:
            logger.error(f"❌ 发生错误: {e}")
            page.screenshot(path="output/xhs_analysis/error.png")
            browser.close()

def main():
    """主函数"""
    output_dir = Path("output/xhs_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("🔍 小红书页面结构分析")
    logger.info("=" * 60)
    
    analyze_page_structure()
    
    logger.info("\n" + "=" * 60)
    logger.info("📊 分析结果已保存到 output/xhs_analysis/ 目录")
    logger.info("请查看截图和HTML源码，找到正确的选择器")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()

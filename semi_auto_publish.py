#!/usr/bin/env python3
"""
半自动发布脚本
用户手动：1. 点击"上传图文" 2. 上传图片
脚本自动：填写标题、内容、点击发布
"""

import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from loguru import logger

def semi_auto_publish():
    """半自动发布"""
    
    cookie_file = Path("cookies/xhs_cookies.json")
    content_file = Path("output/contract_xhs/xhs_content.json")
    
    with open(content_file, 'r', encoding='utf-8') as f:
        content_data = json.load(f)
    
    image_paths = [Path(p) for p in content_data['images']]
    title = content_data['title']
    content = content_data['content']
    tags = content_data['tags']
    
    full_content = content + "\n\n" + " ".join([f"#{tag}" for tag in tags])
    
    logger.info("=" * 70)
    logger.info("🤝 小红书半自动发布")
    logger.info("=" * 70)
    logger.info("")
    logger.info("📋 准备好的内容:")
    logger.info(f"  标题: {title}")
    logger.info(f"  图片: {len(image_paths)} 张")
    logger.info(f"  图片位置: output/contract_xhs/")
    logger.info("")
    logger.info("=" * 70)
    logger.info("🙋 需要您手动操作的部分:")
    logger.info("=" * 70)
    logger.info("1. 浏览器打开后，点击 '上传图文' 标签")
    logger.info("2. 上传以下3张图片（按顺序）:")
    for i, img in enumerate(image_paths, 1):
        logger.info(f"     {i}. {img.name}")
    logger.info("3. 等待图片上传完成，看到编辑界面")
    logger.info("4. 完成后，脚本会自动填写标题和内容并发布")
    logger.info("")
    logger.info("=" * 70)
    logger.info("⏳ 5秒后打开浏览器...")
    logger.info("=" * 70)
    time.sleep(5)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            storage_state=str(cookie_file),
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        try:
            # 打开发布页面
            logger.info("📄 打开发布页面...")
            page.goto("https://creator.xiaohongshu.com/publish/publish",
                     wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            
            logger.info("")
            logger.info("=" * 70)
            logger.info("👆 请在浏览器中手动操作:")
            logger.info("=" * 70)
            logger.info("1. 点击 '上传图文' 标签")
            logger.info("2. 上传3张图片（位于 output/contract_xhs/）")
            logger.info("3. 等待进入编辑界面（看到标题和内容输入框）")
            logger.info("")
            logger.info("⏳ 脚本将等待60秒，请在此期间完成上传...")
            logger.info("=" * 70)
            
            # 等待用户操作
            for i in range(60, 0, -10):
                logger.info(f"  还剩 {i} 秒...")
                time.sleep(10)
            
            logger.info("")
            logger.info("=" * 70)
            logger.info("🤖 开始自动填写...")
            logger.info("=" * 70)
            
            # 检查是否进入编辑界面
            has_editor = page.evaluate("""
            (() => {
                const inputs = document.querySelectorAll('input[placeholder], [contenteditable="true"], textarea');
                return inputs.length > 0;
            })()
            """)
            
            if not has_editor:
                logger.warning("⚠️ 未检测到编辑界面，请确保已上传图片")
                logger.info("按回车继续，或Ctrl+C取消...")
                input()
            
            page.screenshot(path="output/semi/01_before_fill.png")
            
            # 自动填写标题
            logger.info("📝 自动填写标题...")
            title_result = page.evaluate(f"""
            (() => {{
                const inputs = document.querySelectorAll('input');
                for (const input of inputs) {{
                    const ph = input.placeholder || '';
                    if ((ph.includes('标题') || ph.includes('填写')) && !ph.includes('搜索')) {{
                        input.focus();
                        input.value = {json.dumps(title)};
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return '✅ 已填写标题';
                    }}
                }}
                return '❌ 未找到标题输入框';
            }})()
            """)
            logger.info(f"  {title_result}")
            time.sleep(1)
            
            # 自动填写内容
            logger.info("📝 自动填写内容...")
            content_result = page.evaluate(f"""
            (() => {{
                const editors = document.querySelectorAll('[contenteditable="true"], textarea');
                for (const editor of editors) {{
                    if (editor.offsetParent === null) continue;
                    
                    const parent = editor.closest('[class*="title"]');
                    if (parent) continue;
                    
                    editor.focus();
                    
                    if (editor.contentEditable === 'true') {{
                        editor.textContent = {json.dumps(full_content)};
                        editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }} else {{
                        editor.value = {json.dumps(full_content)};
                        editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}
                    
                    return '✅ 已填写内容';
                }}
                return '❌ 未找到内容输入框';
            }})()
            """)
            logger.info(f"  {content_result}")
            time.sleep(2)
            
            page.screenshot(path="output/semi/02_after_fill.png")
            
            logger.info("")
            logger.info("=" * 70)
            logger.success("✅ 标题和内容已自动填写完成！")
            logger.info("=" * 70)
            logger.info("")
            logger.info("📋 请检查浏览器中的内容是否正确")
            logger.info("")
            logger.info("准备发布...")
            logger.info("  - 按回车键：自动点击发布按钮")
            logger.info("  - 按 Ctrl+C：取消发布，手动操作")
            logger.info("=" * 70)
            
            try:
                input("按回车继续发布...")
            except KeyboardInterrupt:
                logger.info("\\n已取消自动发布，请手动操作")
                logger.info("⏳ 保持浏览器打开120秒...")
                time.sleep(120)
                return
            
            # 自动点击发布
            logger.info("📤 自动点击发布按钮...")
            publish_result = page.evaluate("""
            (() => {
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    const text = btn.textContent.trim();
                    if (text === '发布' && btn.offsetParent !== null) {
                        btn.click();
                        return '✅ 已点击发布按钮';
                    }
                }
                return '❌ 未找到发布按钮';
            })()
            """)
            logger.info(f"  {publish_result}")
            
            if "未找到" in publish_result:
                logger.warning("⚠️ 请手动点击发布按钮")
            
            time.sleep(5)
            page.screenshot(path="output/semi/03_after_publish.png")
            
            logger.info("")
            logger.success("=" * 70)
            logger.success("🎉 发布流程完成！")
            logger.success("=" * 70)
            logger.info("⏳ 保持浏览器打开10秒...")
            time.sleep(10)
            
        except KeyboardInterrupt:
            logger.info("\\n用户取消")
        except Exception as e:
            logger.error(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            page.screenshot(path="output/semi/error.png")
            time.sleep(30)
        finally:
            context.storage_state(path=str(cookie_file))
            browser.close()

if __name__ == "__main__":
    Path("output/semi").mkdir(parents=True, exist_ok=True)
    semi_auto_publish()

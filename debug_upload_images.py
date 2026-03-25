#!/usr/bin/env python3
"""
调试图片上传过程
"""

import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from loguru import logger

def debug_upload():
    """调试图片上传"""
    
    cookie_file = Path("cookies/xhs_cookies.json")
    content_file = Path("output/contract_xhs/xhs_content.json")
    
    with open(content_file, 'r', encoding='utf-8') as f:
        content_data = json.load(f)
    
    image_paths = [Path(p) for p in content_data['images']]
    
    logger.info("🚀 开始调试图片上传")
    logger.info(f"图片数量: {len(image_paths)}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        context = browser.new_context(
            storage_state=str(cookie_file),
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        try:
            # 1. 访问页面
            logger.info("📄 步骤1: 访问发布页面")
            page.goto("https://creator.xiaohongshu.com/publish/publish",
                     wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            page.screenshot(path="output/debug/step1_initial.png")
            
            # 2. 点击上传图文
            logger.info("📄 步骤2: 点击上传图文标签")
            result = page.evaluate("""
            (() => {
                const tabs = Array.from(document.querySelectorAll('div[class*="tab"]'));
                const imageTab = tabs.find(t => t.textContent.includes('上传图文'));
                if (imageTab) {
                    console.log('找到上传图文标签:', imageTab);
                    imageTab.click();
                    return '已点击上传图文';
                }
                return '未找到';
            })()
            """)
            logger.info(f"  {result}")
            time.sleep(3)
            page.screenshot(path="output/debug/step2_clicked_tab.png")
            
            # 3. 查找所有file input
            logger.info("📄 步骤3: 查找文件输入框")
            file_inputs_info = page.evaluate("""
            (() => {
                const inputs = document.querySelectorAll('input[type="file"]');
                return Array.from(inputs).map((input, i) => ({
                    index: i,
                    visible: input.offsetParent !== null,
                    accept: input.accept,
                    multiple: input.multiple,
                    className: input.className
                }));
            })()
            """)
            logger.info(f"  找到 {len(file_inputs_info)} 个文件输入框:")
            for info in file_inputs_info:
                logger.info(f"    [{info['index']}] visible={info['visible']}, multiple={info['multiple']}, accept={info['accept']}")
            
            # 4. 尝试上传第一张图片到第一个可见的input
            logger.info("📄 步骤4: 上传图片")
            
            # 找到正确的input（图文上传的）
            file_input = page.locator('input[type="file"]').nth(0)
            
            logger.info(f"  上传第1张图片: {image_paths[0]}")
            file_input.set_input_files(str(image_paths[0]))
            time.sleep(5)
            
            page.screenshot(path="output/debug/step3_after_first_upload.png")
            
            # 检查页面变化
            logger.info("📄 步骤5: 检查页面变化")
            page_state = page.evaluate("""
            (() => {
                // 查找图片预览
                const images = document.querySelectorAll('img[src*="blob:"], img[src*="data:"]');
                // 查找编辑区域
                const editors = document.querySelectorAll('[contenteditable="true"], textarea');
                // 查找标题输入
                const titles = document.querySelectorAll('input[placeholder*="标题"]');
                
                return {
                    imageCount: images.length,
                    editorCount: editors.length,
                    titleCount: titles.length
                };
            })()
            """)
            logger.info(f"  页面状态: {page_state}")
            
            # 如果没有进入编辑模式，尝试点击"上传图片"按钮
            logger.info("📄 步骤6: 尝试查找并点击上传按钮")
            upload_button = page.evaluate("""
            (() => {
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    if (btn.textContent.includes('上传图片')) {
                        btn.click();
                        return '点击了上传图片按钮';
                    }
                }
                return '未找到上传图片按钮';
            })()
            """)
            logger.info(f"  {upload_button}")
            time.sleep(2)
            
            page.screenshot(path="output/debug/step4_after_button_click.png")
            
            # 如果点击了按钮，再次尝试上传
            if "点击了" in upload_button:
                logger.info("📄 步骤7: 按钮点击后重新上传图片")
                file_input = page.locator('input[type="file"]').first
                
                # 尝试上传多张
                all_paths = [str(p) for p in image_paths]
                try:
                    file_input.set_input_files(all_paths)
                    logger.info(f"  尝试一次上传所有 {len(all_paths)} 张图片")
                except Exception as e:
                    logger.info(f"  一次上传失败: {e}，改为逐张上传")
                    for i, img_path in enumerate(image_paths):
                        logger.info(f"  上传第 {i+1} 张...")
                        file_input = page.locator('input[type="file"]').first
                        file_input.set_input_files(str(img_path))
                        time.sleep(2)
                
                time.sleep(5)
                page.screenshot(path="output/debug/step5_all_uploaded.png")
            
            # 最终状态检查
            logger.info("📄 步骤8: 检查最终状态")
            final_state = page.evaluate("""
            (() => {
                const images = document.querySelectorAll('img');
                const editors = document.querySelectorAll('[contenteditable="true"], textarea');
                const titles = document.querySelectorAll('input[placeholder*="标题"], input[placeholder*="填写"]');
                
                return {
                    totalImages: images.length,
                    editors: Array.from(editors).map(e => ({
                        tag: e.tagName,
                        visible: e.offsetParent !== null,
                        placeholder: e.placeholder || ''
                    })),
                    titles: Array.from(titles).map(t => ({
                        visible: t.offsetParent !== null,
                        placeholder: t.placeholder
                    }))
                };
            })()
            """)
            
            logger.info("  最终状态:")
            logger.info(f"    图片数量: {final_state['totalImages']}")
            logger.info(f"    编辑器数量: {len(final_state['editors'])}")
            for i, editor in enumerate(final_state['editors']):
                logger.info(f"      编辑器{i}: {editor}")
            logger.info(f"    标题输入框数量: {len(final_state['titles'])}")
            for i, title in enumerate(final_state['titles']):
                logger.info(f"      标题{i}: {title}")
            
            page.screenshot(path="output/debug/step6_final_state.png")
            
            # 保持打开60秒观察
            logger.info("⏳ 保持浏览器打开60秒...")
            time.sleep(60)
            
        except Exception as e:
            logger.error(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            page.screenshot(path="output/debug/error.png")
            time.sleep(60)
        finally:
            browser.close()

if __name__ == "__main__":
    Path("output/debug").mkdir(parents=True, exist_ok=True)
    debug_upload()

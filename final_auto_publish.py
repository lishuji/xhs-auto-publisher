#!/usr/bin/env python3
"""
最终版自动发布脚本 - 使用真实的点击和等待
"""

import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from loguru import logger

def final_publish():
    """最终版发布"""
    
    cookie_file = Path("cookies/xhs_cookies.json")
    content_file = Path("output/contract_xhs/xhs_content.json")
    
    with open(content_file, 'r', encoding='utf-8') as f:
        content_data = json.load(f)
    
    image_paths = [Path(p) for p in content_data['images']]
    title = content_data['title']
    content = content_data['content']
    tags = content_data['tags']
    
    # 拼接完整内容
    full_content = content
    if tags:
        tag_text = " ".join([f"#{tag}" for tag in tags])
        full_content += f"\n\n{tag_text}"
    
    logger.info("=" * 60)
    logger.info("🚀 小红书自动发布 - 最终版")
    logger.info("=" * 60)
    logger.info(f"标题: {title}")
    logger.info(f"图片: {len(image_paths)} 张")
    logger.info("")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=800)
        context = browser.new_context(
            storage_state=str(cookie_file),
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        try:
            # 步骤1: 访问页面
            logger.info("📄 步骤1: 访问发布页面...")
            page.goto("https://creator.xiaohongshu.com/publish/publish",
                     wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            page.screenshot(path="output/final/01_loaded.png")
            logger.success("✅ 页面加载完成")
            
            # 步骤2: 点击"上传图文"标签并等待页面切换
            logger.info("📄 步骤2: 切换到图文上传模式...")
            
            # 先找到第二个标签（上传图文）
            page.evaluate("""
            (() => {
                const tabs = Array.from(document.querySelectorAll('div[class*="tab"]'));
                console.log('所有标签:', tabs.map(t => t.textContent));
                const imageTab = tabs.find(t => t.textContent.includes('上传图文'));
                if (imageTab) {
                    imageTab.click();
                    console.log('点击了上传图文标签');
                }
            })()
            """)
            
            # 等待页面切换 - 等待正确的file input出现（accept包含图片格式）
            logger.info("  等待页面切换...")
            try:
                # 等待accept包含图片格式的input出现
                page.wait_for_function("""
                () => {
                    const inputs = document.querySelectorAll('input[type="file"]');
                    for (const input of inputs) {
                        if (input.accept && (input.accept.includes('.jpg') || input.accept.includes('.png') || input.accept.includes('.jpeg') || input.accept.includes('image/'))) {
                            return true;
                        }
                    }
                    return false;
                }
                """, timeout=10000)
                logger.success("✅ 图文上传模式已就绪")
            except PlaywrightTimeout:
                logger.warning("⚠️ 未检测到图片input，继续尝试...")
            
            time.sleep(2)
            page.screenshot(path="output/final/02_switched.png")
            
            # 步骤3: 查找正确的上传按钮并点击
            logger.info("📄 步骤3: 点击上传图片按钮...")
            
            # 查找并点击红色的"上传图片"按钮
            upload_btn_clicked = page.evaluate("""
            (() => {
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    const text = btn.textContent.trim();
                    if (text === '上传图片' || text.includes('上传图片')) {
                        console.log('找到上传图片按钮:', btn);
                        btn.click();
                        return true;
                    }
                }
                return false;
            })()
            """)
            
            if upload_btn_clicked:
                logger.success("✅ 已点击上传图片按钮")
                time.sleep(1)
            else:
                logger.info("  未找到上传图片按钮，直接尝试使用file input")
            
            # 步骤4: 上传图片
            logger.info("📄 步骤4: 上传图片...")
            
            # 查找所有file input并找到接受图片的那个
            file_inputs = page.query_selector_all('input[type="file"]')
            logger.info(f"  找到 {len(file_inputs)} 个文件输入框")
            
            correct_input = None
            for i, file_input in enumerate(file_inputs):
                accept = file_input.get_attribute("accept") or ""
                logger.info(f"    Input[{i}]: accept='{accept}'")
                if "image" in accept.lower() or ".jpg" in accept or ".png" in accept or ".jpeg" in accept:
                    correct_input = file_input
                    logger.success(f"    ✅ 使用 Input[{i}] (接受图片格式)")
                    break
            
            if not correct_input and file_inputs:
                # 如果没找到特定的，使用第一个
                correct_input = file_inputs[0]
                logger.info("    使用第一个file input")
            
            if correct_input:
                # 尝试一次上传所有图片
                all_paths = [str(p) for p in image_paths]
                try:
                    correct_input.set_input_files(all_paths)
                    logger.success(f"✅ 已上传 {len(all_paths)} 张图片")
                    time.sleep(5)
                except Exception as e:
                    logger.info(f"  一次上传失败: {e}，改为逐张上传")
                    for i, img_path in enumerate(image_paths, 1):
                        logger.info(f"  上传第 {i}/{len(image_paths)} 张...")
                        correct_input.set_input_files(str(img_path))
                        time.sleep(2)
                
                time.sleep(3)
                page.screenshot(path="output/final/03_images_uploaded.png")
            else:
                logger.error("❌ 未找到合适的文件输入框")
                page.screenshot(path="output/final/error_no_input.png")
                return False
            
            # 步骤5: 等待进入编辑界面
            logger.info("📄 步骤5: 等待进入编辑界面...")
            
            try:
                # 等待标题或内容输入框出现
                page.wait_for_function("""
                () => {
                    const inputs = document.querySelectorAll('input[placeholder], [contenteditable="true"], textarea');
                    return inputs.length > 0;
                }
                """, timeout=10000)
                logger.success("✅ 编辑界面已加载")
            except PlaywrightTimeout:
                logger.warning("⚠️ 未检测到编辑界面，继续尝试...")
            
            time.sleep(2)
            page.screenshot(path="output/final/04_editor_loaded.png")
            
            # 步骤6: 填写标题
            logger.info("📄 步骤6: 填写标题...")
            
            title_result = page.evaluate(f"""
            (() => {{
                // 查找所有input
                const inputs = document.querySelectorAll('input');
                for (const input of inputs) {{
                    const ph = input.placeholder || '';
                    // 排除搜索框等
                    if (ph.includes('标题') || ph.includes('填写') || ph.includes('请输入')) {{
                        if (!ph.includes('搜索') && !ph.includes('话题')) {{
                            input.focus();
                            input.value = {json.dumps(title)};
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return '已填写标题: ' + ph;
                        }}
                    }}
                }}
                return '未找到标题输入框';
            }})()
            """)
            logger.info(f"  {title_result}")
            time.sleep(1)
            page.screenshot(path="output/final/05_title_filled.png")
            
            # 步骤7: 填写内容
            logger.info("📄 步骤7: 填写内容...")
            
            content_result = page.evaluate(f"""
            (() => {{
                // 查找contenteditable或textarea
                const editors = document.querySelectorAll('[contenteditable="true"], textarea');
                for (const editor of editors) {{
                    // 检查是否可见
                    if (editor.offsetParent === null) continue;
                    
                    // 跳过标题相关的
                    const parent = editor.closest('[class*="title"]');
                    if (parent && parent.className.toLowerCase().includes('title')) continue;
                    
                    editor.focus();
                    
                    if (editor.contentEditable === 'true') {{
                        editor.textContent = {json.dumps(full_content)};
                        editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }} else {{
                        editor.value = {json.dumps(full_content)};
                        editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        editor.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                    
                    return '已填写内容，长度: ' + {json.dumps(full_content)}.length;
                }}
                return '未找到内容输入框';
            }})()
            """)
            logger.info(f"  {content_result}")
            time.sleep(2)
            page.screenshot(path="output/final/06_content_filled.png")
            
            # 步骤8: 查找并点击发布按钮
            logger.info("📄 步骤8: 点击发布按钮...")
            
            publish_result = page.evaluate("""
            (() => {
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    const text = btn.textContent.trim();
                    // 查找"发布"按钮（不是"发布笔记"这个大按钮）
                    if (text === '发布' && btn.offsetParent !== null) {
                        console.log('找到发布按钮:', btn);
                        btn.click();
                        return '已点击发布按钮';
                    }
                }
                return '未找到发布按钮';
            })()
            """)
            logger.info(f"  {publish_result}")
            time.sleep(5)
            page.screenshot(path="output/final/07_after_publish.png")
            
            # 检查是否发布成功
            current_url = page.url
            logger.info(f"  当前URL: {current_url}")
            
            if "publish" not in current_url.lower() or "success" in current_url.lower():
                logger.success("🎉 发布成功！")
                time.sleep(3)
                page.screenshot(path="output/final/08_success.png")
                return True
            else:
                logger.warning("⚠️ 可能未成功，请检查截图")
                time.sleep(10)
                return False
            
        except Exception as e:
            logger.error(f"❌ 发布失败: {e}")
            import traceback
            traceback.print_exc()
            page.screenshot(path="output/final/error.png")
            time.sleep(30)
            return False
        finally:
            context.storage_state(path=str(cookie_file))
            browser.close()

if __name__ == "__main__":
    Path("output/final").mkdir(parents=True, exist_ok=True)
    
    logger.info("⚠️  准备开始真实发布")
    logger.info("按 Ctrl+C 取消，或等待3秒自动开始...")
    time.sleep(3)
    
    success = final_publish()
    
    if success:
        logger.success("=" * 60)
        logger.success("🎉 发布完成！")
        logger.success("=" * 60)
    else:
        logger.error("=" * 60)
        logger.error("❌ 发布失败，请查看截图")
        logger.error("=" * 60)

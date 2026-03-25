#!/usr/bin/env python3
"""
增强版小红书自动发布脚本
使用JavaScript注入和更可靠的元素操作方法
"""

import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from loguru import logger

def auto_publish_to_xhs(title, content, tags, image_paths, dry_run=False):
    """自动发布到小红书"""
    
    cookie_file = Path("cookies/xhs_cookies.json")
    if not cookie_file.exists():
        logger.error("❌ Cookie文件不存在，请先运行 python main.py login")
        return False
    
    logger.info("=" * 60)
    logger.info("🚀 小红书自动发布")
    logger.info("=" * 60)
    logger.info(f"📄 标题: {title}")
    logger.info(f"🖼️  图片: {len(image_paths)} 张")
    logger.info(f"🏷️  标签: {len(tags)} 个")
    logger.info("")
    
    with sync_playwright() as p:
        # 启动浏览器（非headless便于观察）
        browser = p.chromium.launch(
            headless=False,
            slow_mo=500  # 每个操作延迟500ms，更像人类
        )
        
        context = browser.new_context(
            storage_state=str(cookie_file),
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        
        page = context.new_page()
        
        try:
            # ========== 步骤1: 访问发布页面 ==========
            logger.info("📄 步骤1: 访问发布页面...")
            page.goto("https://creator.xiaohongshu.com/publish/publish", 
                     wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)  # 额外等待页面完全加载
            
            page.screenshot(path="output/auto_step1_loaded.png")
            logger.success("✅ 页面已加载")
            
            # ========== 步骤2: 点击"上传图文"标签 ==========
            logger.info("📄 步骤2: 切换到图文发布模式...")
            
            # 使用JavaScript查找并点击
            js_click_tab = """
            (() => {
                const tabs = document.querySelectorAll('.creator-tab, [class*="tab"]');
                for (const tab of tabs) {
                    if (tab.textContent.includes('上传图文')) {
                        tab.click();
                        return '找到并点击了上传图文标签';
                    }
                }
                return '未找到上传图文标签';
            })()
            """
            
            result = page.evaluate(js_click_tab)
            logger.info(f"  {result}")
            time.sleep(2)
            
            page.screenshot(path="output/auto_step2_clicked_tab.png")
            
            # ========== 步骤3: 上传图片 ==========
            logger.info("📄 步骤3: 上传图片...")
            
            for i, img_path in enumerate(image_paths, 1):
                logger.info(f"  📷 上传第 {i}/{len(image_paths)} 张...")
                
                # 查找文件输入框
                file_inputs = page.query_selector_all('input[type="file"]')
                if file_inputs:
                    # 使用第一个可见的文件输入
                    for file_input in file_inputs:
                        try:
                            file_input.set_input_files(str(img_path))
                            logger.success(f"    ✅ 第 {i} 张上传成功")
                            time.sleep(3)  # 等待上传
                            break
                        except Exception as e:
                            logger.debug(f"    尝试失败: {e}")
                            continue
            
            time.sleep(5)  # 等待所有图片处理完成
            page.screenshot(path="output/auto_step3_uploaded.png")
            logger.success("✅ 图片上传完成")
            
            # ========== 步骤4: 填写标题 ==========
            logger.info("📄 步骤4: 填写标题...")
            
            # 使用JavaScript查找并填写标题
            js_fill_title = f"""
            (() => {{
                const inputs = document.querySelectorAll('input[placeholder], input.title-input, #post-textarea');
                for (const input of inputs) {{
                    const placeholder = input.placeholder || '';
                    if (placeholder.includes('标题') || placeholder.includes('填写') || input.classList.contains('title')) {{
                        input.focus();
                        input.value = {json.dumps(title)};
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return '已填写标题: ' + placeholder;
                    }}
                }}
                return '未找到标题输入框';
            }})()
            """
            
            title_result = page.evaluate(js_fill_title)
            logger.info(f"  {title_result}")
            time.sleep(1)
            
            page.screenshot(path="output/auto_step4_title.png")
            
            # ========== 步骤5: 填写正文 ==========
            logger.info("📄 步骤5: 填写正文...")
            
            # 拼接正文和标签
            full_content = content
            if tags:
                tag_text = " ".join([f"#{tag}" for tag in tags])
                full_content += f"\n\n{tag_text}"
            
            # 使用JavaScript查找并填写正文
            js_fill_content = f"""
            (() => {{
                // 查找内容编辑器
                const editors = document.querySelectorAll('[contenteditable="true"], textarea, .content-input');
                for (const editor of editors) {{
                    // 跳过标题输入框
                    const parent = editor.closest('.title-container, .title-input');
                    if (parent) continue;
                    
                    editor.focus();
                    
                    // 如果是contenteditable
                    if (editor.contentEditable === 'true') {{
                        editor.innerText = {json.dumps(full_content)};
                        editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }} else {{
                        // 如果是textarea
                        editor.value = {json.dumps(full_content)};
                        editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        editor.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                    
                    return '已填写正文，长度: ' + {json.dumps(full_content)}.length;
                }}
                return '未找到正文输入框';
            }})()
            """
            
            content_result = page.evaluate(js_fill_content)
            logger.info(f"  {content_result}")
            time.sleep(2)
            
            page.screenshot(path="output/auto_step5_content.png")
            logger.success("✅ 内容填写完成")
            
            # ========== 步骤6: 发布 ==========
            if dry_run:
                logger.info("📄 步骤6: Dry-run模式，跳过发布")
                logger.info("⏳ 保持浏览器打开30秒，请检查内容...")
                time.sleep(30)
                logger.success("✅ Dry-run测试完成")
                return True
            else:
                logger.info("📄 步骤6: 点击发布按钮...")
                
                # 使用JavaScript查找并点击发布按钮
                js_click_publish = """
                (() => {
                    const buttons = document.querySelectorAll('button');
                    for (const btn of buttons) {
                        if (btn.textContent.includes('发布') && !btn.textContent.includes('发布笔记')) {
                            btn.click();
                            return '已点击发布按钮';
                        }
                    }
                    return '未找到发布按钮';
                })()
                """
                
                publish_result = page.evaluate(js_click_publish)
                logger.info(f"  {publish_result}")
                time.sleep(5)
                
                page.screenshot(path="output/auto_step6_published.png")
                
                # 检查是否发布成功
                current_url = page.url
                if "publish" not in current_url.lower() or "success" in current_url.lower():
                    logger.success("🎉 笔记发布成功！")
                    time.sleep(5)  # 等待跳转
                    return True
                else:
                    logger.warning("⚠️ 可能未成功发布，请检查截图")
                    time.sleep(10)
                    return False
            
        except Exception as e:
            logger.error(f"❌ 发布失败: {e}")
            import traceback
            traceback.print_exc()
            
            page.screenshot(path="output/auto_error.png")
            logger.info("📷 错误截图: output/auto_error.png")
            
            # 保持浏览器打开以便调试
            logger.info("⏳ 保持浏览器打开60秒以便检查...")
            time.sleep(60)
            return False
            
        finally:
            # 保存Cookie
            context.storage_state(path=str(cookie_file))
            browser.close()

def main():
    """主函数"""
    # 读取内容
    content_file = Path("output/contract_xhs/xhs_content.json")
    
    if not content_file.exists():
        logger.error("❌ 内容文件不存在，请先运行 create_xhs_content_from_website.py")
        return
    
    with open(content_file, 'r', encoding='utf-8') as f:
        content_data = json.load(f)
    
    # 转换图片路径
    image_paths = [Path(p) for p in content_data['images']]
    
    # 确认是否真实发布
    logger.info("=" * 60)
    logger.info("⚠️  即将自动发布到小红书")
    logger.info("=" * 60)
    logger.info(f"标题: {content_data['title']}")
    logger.info(f"图片: {len(image_paths)} 张")
    logger.info(f"标签: {', '.join(content_data['tags'])}")
    logger.info("")
    
    # 这里可以设置为 dry_run=False 进行真实发布
    # 建议先用 dry_run=True 测试
    dry_run = input("是否真实发布？(输入 yes 真实发布，其他为测试模式): ").lower() == 'yes'
    
    if dry_run:
        logger.info("🔍 测试模式: 不会真正发布")
    else:
        logger.warning("⚠️  真实发布模式: 将会实际发布笔记")
    
    logger.info("")
    
    # 执行发布
    success = auto_publish_to_xhs(
        title=content_data['title'],
        content=content_data['content'],
        tags=content_data['tags'],
        image_paths=image_paths,
        dry_run=not dry_run  # 如果用户输入yes，dry_run=False
    )
    
    if success:
        logger.success("=" * 60)
        logger.success("🎉 发布流程完成！")
        logger.success("=" * 60)
    else:
        logger.error("=" * 60)
        logger.error("❌ 发布流程失败")
        logger.error("=" * 60)
        logger.info("💡 建议:")
        logger.info("  1. 查看截图文件: output/auto_*.png")
        logger.info("  2. 检查是否需要手动操作")
        logger.info("  3. 或参考 手动发布指南.md")

if __name__ == "__main__":
    main()

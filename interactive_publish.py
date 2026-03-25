#!/usr/bin/env python3
"""
交互式发布脚本 - 引导用户完成发布
"""

import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from loguru import logger

def interactive_publish():
    """交互式发布"""
    
    cookie_file = Path("cookies/xhs_cookies.json")
    content_file = Path("output/contract_xhs/xhs_content.json")
    
    with open(content_file, 'r', encoding='utf-8') as f:
        content_data = json.load(f)
    
    image_paths = [Path(p).absolute() for p in content_data['images']]
    title = content_data['title']
    content = content_data['content']
    tags = content_data['tags']
    
    full_content = content + "\n\n" + " ".join([f"#{tag}" for tag in tags])
    
    print("\n" + "=" * 70)
    print("🚀 小红书交互式发布")
    print("=" * 70)
    print(f"\n📋 准备发布的内容:")
    print(f"   标题: {title}")
    print(f"   图片: {len(image_paths)} 张")
    print(f"\n📁 图片位置:")
    for i, img in enumerate(image_paths, 1):
        print(f"   {i}. {img}")
    
    print("\n" + "=" * 70)
    print("📖 操作说明:")
    print("=" * 70)
    print("1. 浏览器将自动打开小红书发布页面")
    print("2. 请手动完成以下操作：")
    print("   - 点击页面上的 '上传图文' 标签")
    print("   - 上传上面显示的3张图片")
    print("   - 等待图片上传完成，进入编辑界面")
    print("3. 完成后回到终端，按回车键")
    print("4. 脚本将自动填写标题、内容并发布")
    print("=" * 70)
    
    input("\n按回车键开始... ")
    
    logger.info("🌐 启动浏览器...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            storage_state=str(cookie_file),
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        try:
            # 访问发布页面
            logger.info("📄 打开小红书发布页面...")
            page.goto("https://creator.xiaohongshu.com/publish/publish",
                     wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            
            print("\n" + "=" * 70)
            print("👆 现在请在浏览器中操作:")
            print("=" * 70)
            print("1. 点击 '上传图文' 标签（在页面顶部）")
            print("2. 点击上传按钮，选择3张图片上传")
            print("   图片位置: output/contract_xhs/")
            print("   - image1_title.jpg")
            print("   - image2_list.jpg")  
            print("   - image3_guide.jpg")
            print("3. 等待图片上传完成")
            print("4. 看到编辑界面（标题和内容输入框）后")
            print("=" * 70)
            
            input("\n✅ 完成图片上传后，按回车继续... ")
            
            # 截图当前状态
            page.screenshot(path="output/publish/01_before_auto.png")
            logger.info("📷 已保存当前截图")
            
            # 检查是否进入编辑模式
            logger.info("🔍 检查编辑界面...")
            has_editor = page.evaluate("""
            (() => {
                const inputs = document.querySelectorAll('input[placeholder], [contenteditable="true"], textarea');
                return inputs.length > 0;
            })()
            """)
            
            if not has_editor:
                logger.warning("⚠️ 未检测到编辑界面")
                print("\n⚠️  还没有进入编辑界面")
                print("请确保已上传图片并进入编辑页面")
                input("准备好后按回车继续，或按Ctrl+C取消... ")
            
            # 自动填写标题
            logger.info("✍️  自动填写标题...")
            title_result = page.evaluate(f"""
            (() => {{
                const inputs = document.querySelectorAll('input');
                for (const input of inputs) {{
                    const ph = input.placeholder || '';
                    if ((ph.includes('标题') || ph.includes('填写') || ph.includes('请输入')) 
                        && !ph.includes('搜索') && !ph.includes('话题')) {{
                        input.focus();
                        input.value = {json.dumps(title)};
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return true;
                    }}
                }}
                return false;
            }})()
            """)
            
            if title_result:
                logger.success("✅ 标题已填写")
            else:
                logger.warning("⚠️ 未找到标题输入框")
            
            time.sleep(1)
            
            # 自动填写内容
            logger.info("✍️  自动填写内容...")
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
                    
                    return true;
                }}
                return false;
            }})()
            """)
            
            if content_result:
                logger.success("✅ 内容已填写")
            else:
                logger.warning("⚠️ 未找到内容输入框")
            
            time.sleep(2)
            page.screenshot(path="output/publish/02_after_fill.png")
            
            print("\n" + "=" * 70)
            print("✅ 标题和内容已自动填写！")
            print("=" * 70)
            print("📋 请在浏览器中检查内容是否正确")
            print("\n准备发布...")
            print("  - 输入 yes 并按回车: 自动点击发布")
            print("  - 直接按回车: 手动点击发布")
            print("  - 按 Ctrl+C: 取消")
            print("=" * 70)
            
            choice = input("\n输入yes自动发布，或直接回车手动发布: ").strip().lower()
            
            if choice == 'yes':
                logger.info("📤 自动点击发布...")
                publish_result = page.evaluate("""
                (() => {
                    const buttons = document.querySelectorAll('button');
                    for (const btn of buttons) {
                        const text = btn.textContent.trim();
                        if (text === '发布' && btn.offsetParent !== null) {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                })()
                """)
                
                if publish_result:
                    logger.success("✅ 已点击发布按钮")
                    time.sleep(3)
                    page.screenshot(path="output/publish/03_published.png")
                    
                    print("\n" + "=" * 70)
                    print("🎉 发布完成！")
                    print("=" * 70)
                    time.sleep(5)
                else:
                    logger.warning("⚠️ 未找到发布按钮，请手动点击")
                    input("手动点击发布后，按回车关闭浏览器... ")
            else:
                print("\n请在浏览器中手动点击 '发布' 按钮")
                input("发布完成后按回车关闭浏览器... ")
                page.screenshot(path="output/publish/03_manual.png")
            
            logger.success("=" * 60)
            logger.success("🎉 发布流程完成！")
            logger.success("=" * 60)
            
        except KeyboardInterrupt:
            logger.info("\n用户取消")
        except Exception as e:
            logger.error(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            page.screenshot(path="output/publish/error.png")
            input("按回车关闭...")
        finally:
            context.storage_state(path=str(cookie_file))
            browser.close()

if __name__ == "__main__":
    Path("output/publish").mkdir(parents=True, exist_ok=True)
    
    try:
        interactive_publish()
    except KeyboardInterrupt:
        print("\n\n已取消")

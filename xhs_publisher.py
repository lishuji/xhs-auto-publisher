"""小红书 Playwright 自动发布模块 - 模拟浏览器操作发布笔记"""

import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, BrowserContext
from loguru import logger
from config import XHS_COOKIE_FILE, COOKIES_DIR


# ============================
#  第一步：登录并保存 Cookie
# ============================

def login_and_save_cookies():
    """
    手动登录小红书创作者中心并保存 Cookie。
    首次使用时运行此函数，会弹出浏览器窗口供你扫码/手机号登录。
    登录成功后自动保存 Cookie，后续发布无需重复登录。
    """
    logger.info("🔐 启动浏览器，请手动登录小红书...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.goto("https://creator.xiaohongshu.com/login")

        logger.info("⏳ 等待登录完成... 请在浏览器中扫码或输入手机号登录")

        # 等待登录成功后跳转到创作者中心首页
        page.wait_for_url("**/home**", timeout=120_000)

        logger.success("✅ 登录成功！正在保存 Cookie...")

        # 保存浏览器状态（包含 Cookie、localStorage 等）
        COOKIES_DIR.mkdir(parents=True, exist_ok=True)
        context.storage_state(path=str(XHS_COOKIE_FILE))

        logger.success(f"💾 Cookie 已保存至: {XHS_COOKIE_FILE}")
        browser.close()


# ============================
#  第二步：自动发布笔记
# ============================

def _wait_and_click(page: Page, selector: str, timeout: int = 10_000):
    """等待元素出现并点击"""
    page.wait_for_selector(selector, timeout=timeout)
    page.click(selector)


def publish_note(
    title: str,
    content: str,
    tags: list[str],
    image_paths: list[Path],
    dry_run: bool = False,
) -> bool:
    """
    自动发布图文笔记到小红书

    Args:
        title: 笔记标题
        content: 笔记正文
        tags: 话题标签列表
        image_paths: 本地图片路径列表
        dry_run: 试运行模式，填充内容但不点击发布

    Returns:
        bool: 是否发布成功
    """
    if not XHS_COOKIE_FILE.exists():
        logger.error("❌ 未找到 Cookie 文件，请先运行 login_and_save_cookies()")
        return False

    if not image_paths:
        logger.error("❌ 至少需要 1 张图片")
        return False

    logger.info(f"🚀 开始发布笔记: {title}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # 建议先用有界面模式调试，稳定后改 True
        )
        context = browser.new_context(
            storage_state=str(XHS_COOKIE_FILE),
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        try:
            # 1. 打开发布页
            logger.info("📄 打开发布页面...")
            page.goto(
                "https://creator.xiaohongshu.com/publish/publish",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            time.sleep(3)

            # 检查是否需要重新登录
            if "login" in page.url:
                logger.error("❌ Cookie 已失效，请重新登录 (运行 login_and_save_cookies)")
                return False
            
            # 2. 点击"上传图文"标签（页面默认是上传视频）
            logger.info("🖱️  点击'上传图文'标签...")
            try:
                # 尝试多个选择器
                image_tab_selectors = [
                    "div.creator-tab:has-text('上传图文')",
                    ".header-tabs div:has-text('上传图文')",
                    "[class*='creator-tab']:has-text('上传图文')",
                ]
                
                tab_clicked = False
                for selector in image_tab_selectors:
                    try:
                        tab = page.query_selector(selector)
                        if tab and tab.is_visible():
                            tab.click()
                            logger.success("✅ 已点击'上传图文'标签")
                            tab_clicked = True
                            time.sleep(2)
                            break
                    except:
                        continue
                
                if not tab_clicked:
                    logger.warning("⚠️ 未找到'上传图文'标签，尝试继续...")
            except Exception as e:
                logger.warning(f"⚠️ 点击标签失败: {e}，尝试继续...")
            
            # 截图以便调试
            page.screenshot(path="output/debug_after_click_tab.png")
            logger.info("📷 截图已保存: output/debug_after_click_tab.png")

            # 3. 上传图片（逐个上传）
            logger.info(f"📸 上传 {len(image_paths)} 张图片...")
            for i, img_path in enumerate(image_paths, 1):
                logger.info(f"📷 上传第 {i}/{len(image_paths)} 张图片...")
                try:
                    # 查找文件上传输入框
                    file_input = page.locator('input[type="file"]').first
                    file_input.set_input_files(str(img_path))
                    logger.success(f"  ✅ 第 {i} 张图片已上传")
                    time.sleep(2)  # 等待单张图片上传
                except Exception as e:
                    logger.error(f"  ❌ 上传第 {i} 张图片失败: {e}")

            # 等待所有图片上传完成
            logger.info("⏳ 等待所有图片上传完成...")
            time.sleep(5)
            
            # 再次截图
            page.screenshot(path="output/debug_after_upload.png")
            logger.info("📷 上传后截图: output/debug_after_upload.png")

            # 4. 填写标题 - 使用更宽松的选择器
            logger.info(f"✏️ 填写标题: {title}")
            title_selectors = [
                "input[placeholder*='标题']",
                "input[placeholder*='填写']",
                "#post-textarea",
                ".title-input input",
                "input.css-input",
            ]
            
            title_filled = False
            for selector in title_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        logger.info(f"  找到 {len(elements)} 个元素匹配: {selector}")
                        # 使用第一个可见元素
                        for elem in elements:
                            if elem.is_visible():
                                elem.click()
                                time.sleep(0.5)
                                elem.fill(title)
                                logger.success("  ✅ 标题已填写")
                                title_filled = True
                                break
                        if title_filled:
                            break
                except Exception as e:
                    logger.debug(f"  尝试选择器 {selector} 失败: {e}")
                    continue
            
            if not title_filled:
                logger.error("❌ 未能填写标题")
                page.screenshot(path="output/error_no_title_input.png")

            # 5. 填写正文
            logger.info("✏️ 填写正文...")
            # 拼接正文和标签
            full_content = content
            if tags:
                tag_text = " ".join([f"#{tag}" for tag in tags])
                full_content += f"\n\n{tag_text}"

            content_selectors = [
                "div[contenteditable='true']",
                "textarea[placeholder*='正文']",
                "#post-textarea",
                ".content-input",
            ]
            
            content_filled = False
            for selector in content_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        logger.info(f"  找到 {len(elements)} 个内容输入元素: {selector}")
                        for elem in elements:
                            if elem.is_visible():
                                elem.click()
                                time.sleep(0.5)
                                # 尝试不同的输入方法
                                try:
                                    elem.fill(full_content)
                                except:
                                    page.keyboard.type(full_content, delay=10)
                                logger.success("  ✅ 正文已填写")
                                content_filled = True
                                break
                        if content_filled:
                            break
                except Exception as e:
                    logger.debug(f"  尝试选择器 {selector} 失败: {e}")
                    continue
            
            if not content_filled:
                logger.error("❌ 未能填写正文")
                page.screenshot(path="output/error_no_content_input.png")

            time.sleep(2)
            
            # 最终截图
            page.screenshot(path="output/debug_before_publish.png")
            logger.info("📷 发布前截图: output/debug_before_publish.png")

            # 6. 发布
            if dry_run:
                logger.info("🧪 试运行模式，不执行发布。请检查浏览器中的内容。")
                logger.info("⏳ 20 秒后关闭浏览器...")
                time.sleep(20)
            else:
                logger.info("📤 点击发布按钮...")
                publish_selectors = [
                    "button:has-text('发布')",
                    ".publish-btn",
                    "button[type='submit']",
                ]
                
                for selector in publish_selectors:
                    try:
                        btn = page.query_selector(selector)
                        if btn and btn.is_visible():
                            btn.click()
                            logger.success("✅ 已点击发布按钮")
                            time.sleep(5)
                            break
                    except:
                        continue

                # 检查是否发布成功
                if "publish" not in page.url.lower():
                    logger.success("🎉 笔记发布成功！")
                else:
                    logger.warning("⚠️ 可能发布未成功，请检查页面状态")
                    page.screenshot(path="output/after_publish.png")

            # 保存更新后的 Cookie
            context.storage_state(path=str(XHS_COOKIE_FILE))
            return True

        except Exception as e:
            logger.error(f"❌ 发布过程出错: {e}")
            import traceback
            traceback.print_exc()
            # 截图保存错误现场
            error_screenshot = Path("output/error_screenshot.png")
            page.screenshot(path=str(error_screenshot))
            logger.info(f"📷 错误截图已保存: {error_screenshot}")
            return False

        finally:
            browser.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "login":
        login_and_save_cookies()
    else:
        print("用法:")
        print("  python xhs_publisher.py login   # 首次登录保存Cookie")
        print("  请通过 main.py 执行完整发布流程")

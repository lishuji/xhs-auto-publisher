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
                wait_until="networkidle",
            )
            time.sleep(2)

            # 检查是否需要重新登录
            if "login" in page.url:
                logger.error("❌ Cookie 已失效，请重新登录 (运行 login_and_save_cookies)")
                return False

            # 2. 上传图片
            logger.info(f"📸 上传 {len(image_paths)} 张图片...")
            file_input = page.locator('input[type="file"]')
            file_paths_str = [str(p) for p in image_paths]
            file_input.set_input_files(file_paths_str)

            # 等待图片上传完成
            logger.info("⏳ 等待图片上传...")
            time.sleep(5)  # 根据图片大小可能需要更长时间

            # 3. 填写标题
            logger.info(f"✏️ 填写标题: {title}")
            title_input = page.locator('#publish-container input[placeholder]')
            title_input.click()
            title_input.fill(title)

            # 4. 填写正文
            logger.info("✏️ 填写正文...")
            # 拼接正文和标签
            full_content = content
            if tags:
                tag_text = " ".join([f"#{tag}" for tag in tags])
                full_content += f"\n\n{tag_text}"

            content_editor = page.locator('#publish-container div[contenteditable="true"]')
            content_editor.click()
            # 使用 keyboard 逐步输入，模拟真实打字（避免被检测）
            page.keyboard.type(full_content, delay=10)

            time.sleep(1)

            # 5. 发布
            if dry_run:
                logger.info("🧪 试运行模式，不执行发布。请检查浏览器中的内容。")
                logger.info("⏳ 10 秒后关闭浏览器...")
                time.sleep(10)
            else:
                logger.info("📤 点击发布按钮...")
                publish_btn = page.locator('button:has-text("发布")')
                publish_btn.click()
                time.sleep(3)

                # 检查是否发布成功
                if "publish" not in page.url.lower():
                    logger.success("🎉 笔记发布成功！")
                else:
                    logger.warning("⚠️ 可能发布未成功，请检查页面状态")

            # 保存更新后的 Cookie
            context.storage_state(path=str(XHS_COOKIE_FILE))
            return True

        except Exception as e:
            logger.error(f"❌ 发布过程出错: {e}")
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

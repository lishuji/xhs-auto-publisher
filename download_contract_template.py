#!/usr/bin/env python3
"""
下载合同示范文本库的合同模板
"""

import time
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright
from loguru import logger

def get_first_contract_info():
    """获取第一个合同模板的信息和下载链接"""
    logger.info("🌐 启动浏览器获取合同模板信息...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = context.new_page()
        
        try:
            # 访问首页
            logger.info("📄 访问合同示范文本库首页...")
            page.goto("https://htsfwb.samr.gov.cn/", timeout=30000)
            time.sleep(3)
            
            # 关闭弹窗（如果存在）
            try:
                close_button = page.query_selector("button:has-text('我知道了')")
                if close_button:
                    logger.info("💡 关闭使用说明弹窗...")
                    close_button.click()
                    time.sleep(1)
            except:
                pass
            
            # 查找第一个合同模板
            logger.info("🔍 查找第一个合同模板...")
            
            # 尝试多种选择器
            selectors = [
                ".contract-item:first-child",
                ".list-item:first-child",
                "a[href*='Detail']",
                ".contract-list a:first-child",
            ]
            
            first_contract = None
            for selector in selectors:
                elements = page.query_selector_all(selector)
                if elements:
                    first_contract = elements[0]
                    logger.success(f"✅ 找到合同元素，使用选择器: {selector}")
                    break
            
            if not first_contract:
                # 获取页面内容保存以便分析
                page.screenshot(path="output/contract_page.png")
                logger.warning("⚠️ 未找到合同链接，保存截图到 output/contract_page.png")
                
                # 尝试获取所有链接
                all_links = page.query_selector_all("a")
                logger.info(f"📋 页面共有 {len(all_links)} 个链接")
                
                # 查找包含 Detail 的链接
                detail_links = []
                for link in all_links:
                    href = link.get_attribute("href")
                    if href and "Detail" in href:
                        detail_links.append(link)
                
                if detail_links:
                    first_contract = detail_links[0]
                    logger.success(f"✅ 找到Detail链接: {len(detail_links)}个")
            
            if first_contract:
                # 获取合同信息
                contract_title = first_contract.text_content().strip()
                contract_href = first_contract.get_attribute("href")
                
                logger.info(f"📋 合同标题: {contract_title}")
                logger.info(f"🔗 链接: {contract_href}")
                
                # 如果是相对链接，补全为完整URL
                if contract_href and not contract_href.startswith("http"):
                    contract_url = f"https://htsfwb.samr.gov.cn{contract_href}"
                else:
                    contract_url = contract_href
                
                logger.info(f"🌐 完整URL: {contract_url}")
                
                # 访问详情页
                logger.info("📄 访问合同详情页...")
                page.goto(contract_url, timeout=30000)
                time.sleep(2)
                
                # 保存详情页截图
                page.screenshot(path="output/contract_detail.png")
                logger.success("📷 详情页截图保存到 output/contract_detail.png")
                
                # 查找下载按钮/链接
                download_selectors = [
                    "a[href*='download']",
                    "a[href*='.doc']",
                    "a[href*='.docx']",
                    "a[href*='.pdf']",
                    "button:has-text('下载')",
                    "a:has-text('下载')",
                    ".download-btn",
                ]
                
                download_link = None
                for selector in download_selectors:
                    try:
                        element = page.query_selector(selector)
                        if element:
                            download_link = element.get_attribute("href")
                            logger.success(f"✅ 找到下载链接: {selector}")
                            break
                    except:
                        continue
                
                # 获取页面文本内容
                page_content = page.content()
                
                result = {
                    "title": contract_title,
                    "detail_url": contract_url,
                    "download_link": download_link,
                    "page_text": page.text_content("body")[:2000]  # 前2000字符
                }
                
                browser.close()
                return result
            else:
                logger.error("❌ 未能找到任何合同模板链接")
                browser.close()
                return None
                
        except Exception as e:
            logger.error(f"❌ 发生错误: {e}")
            page.screenshot(path="output/error_page.png")
            browser.close()
            return None

def download_file(url: str, save_path: Path):
    """下载文件"""
    logger.info(f"⬇️ 开始下载文件: {url}")
    
    try:
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.success(f"✅ 文件下载成功: {save_path}")
        return True
    except Exception as e:
        logger.error(f"❌ 下载失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 开始获取合同模板...")
    
    # 创建输出目录
    output_dir = Path("output/contracts")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取第一个合同信息
    contract_info = get_first_contract_info()
    
    if contract_info:
        logger.info("=" * 60)
        logger.info("📊 合同信息:")
        logger.info(f"标题: {contract_info['title']}")
        logger.info(f"详情页: {contract_info['detail_url']}")
        logger.info(f"下载链接: {contract_info['download_link']}")
        logger.info("=" * 60)
        
        # 如果有下载链接，下载文件
        if contract_info['download_link']:
            file_extension = ".docx" if ".doc" in contract_info['download_link'] else ".pdf"
            save_path = output_dir / f"contract_template{file_extension}"
            download_file(contract_info['download_link'], save_path)
        
        # 保存合同信息
        import json
        info_path = output_dir / "contract_info.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(contract_info, f, ensure_ascii=False, indent=2)
        logger.success(f"💾 合同信息已保存: {info_path}")
        
        return contract_info
    else:
        logger.error("❌ 未能获取合同信息")
        return None

if __name__ == "__main__":
    main()

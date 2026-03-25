#!/usr/bin/env python3
"""
发布合同文本库内容到小红书
"""

import json
from pathlib import Path
from loguru import logger
from xhs_publisher import publish_note

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🚀 发布合同文本库内容到小红书")
    logger.info("=" * 60)
    
    # 读取内容
    content_file = Path("output/contract_xhs/xhs_content.json")
    with open(content_file, 'r', encoding='utf-8') as f:
        content_data = json.load(f)
    
    logger.info(f"📄 标题: {content_data['title']}")
    logger.info(f"🏷️  标签: {', '.join(content_data['tags'])}")
    logger.info(f"🖼️  图片数量: {len(content_data['images'])}")
    logger.info("")
    
    # 转换图片路径为Path对象
    image_paths = [Path(p) for p in content_data['images']]
    
    # 发布到小红书 (dry-run模式测试)
    dry_run = True  # 改为False可以真实发布
    
    if dry_run:
        logger.info("🔍 Dry-run 模式: 不会真正发布笔记")
    else:
        logger.warning("⚠️  真实发布模式: 将会实际发布笔记")
    
    logger.info("=" * 60)
    
    try:
        success = publish_note(
            title=content_data['title'],
            content=content_data['content'],
            tags=content_data['tags'],
            image_paths=image_paths,
            dry_run=dry_run
        )
        
        if success:
            if dry_run:
                logger.success("✅ Dry-run 测试完成！流程验证成功")
            else:
                logger.success("✅ 笔记发布成功！")
        else:
            logger.error("❌ 发布失败")
            
    except Exception as e:
        logger.error(f"❌ 发布过程出错: {e}")
        raise
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("🎉 发布流程完成！")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()

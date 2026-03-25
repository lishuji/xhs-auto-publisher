#!/usr/bin/env python3
"""
真实发布测试脚本
跳过图片生成，仅测试内容生成和发布流程
"""

import os
import sys
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入项目模块
from content_generator import generate_note
from xhs_publisher import publish_note

def test_content_generation(topic: str):
    """测试内容生成功能"""
    logger.info(f"📝 测试主题: {topic}")
    logger.info("=" * 60)
    
    try:
        # 生成笔记内容
        logger.info("🔄 正在生成笔记内容...")
        note = generate_note(topic)
        
        logger.success(f"✅ 内容生成成功！")
        logger.info(f"📌 标题: {note['title']}")
        logger.info(f"📄 内容长度: {len(note['content'])} 字符")
        logger.info(f"🖼️  图片提示词数量: {len(note['image_prompts'])}")
        logger.info("")
        logger.info("=" * 60)
        logger.info("📄 完整内容:")
        logger.info("=" * 60)
        logger.info(f"标题: {note['title']}")
        logger.info("")
        logger.info(note['content'])
        logger.info("=" * 60)
        
        return note
        
    except Exception as e:
        logger.error(f"❌ 内容生成失败: {e}")
        raise

def test_publish_without_images(topic: str, dry_run: bool = True):
    """测试发布流程（使用简单测试图片）"""
    logger.info("🚀 开始真实发布测试")
    logger.info("=" * 60)
    
    # 1. 生成内容
    note = test_content_generation(topic)
    
    # 2. 创建一个简单的测试图片
    logger.info("")
    logger.info("🖼️  创建测试图片...")
    from PIL import Image, ImageDraw, ImageFont
    
    # 创建输出目录
    output_dir = Path("output/test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建一张简单的测试图片
    img = Image.new('RGB', (1024, 1024), color='#FFE5E5')
    draw = ImageDraw.Draw(img)
    
    # 添加文字
    text = "测试图片\n春季护肤"
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 80)
    except:
        font = ImageFont.load_default()
    
    # 计算文字位置（居中）
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (1024 - text_width) / 2
    y = (1024 - text_height) / 2
    
    draw.text((x, y), text, fill='#FF6B9D', font=font, align='center')
    
    # 保存图片
    test_image_path = output_dir / "test_image.jpg"
    img.save(test_image_path, quality=95)
    logger.success(f"✅ 测试图片已创建: {test_image_path}")
    
    image_paths = [test_image_path]
    
    # 3. 从生成的内容中提取标签（或使用默认标签）
    tags = ["春季护肤", "护肤技巧", "干货分享"]
    
    # 4. 发布到小红书
    logger.info("")
    if dry_run:
        logger.info("🔍 Dry-run 模式: 不会真正发布笔记")
    else:
        logger.info("⚠️  真实发布模式: 将会实际发布笔记")
    
    logger.info("=" * 60)
    
    try:
        publish_note(
            title=note['title'],
            content=note['content'],
            tags=tags,
            image_paths=image_paths,
            dry_run=dry_run
        )
        
        if dry_run:
            logger.success("✅ Dry-run 测试完成！流程验证成功")
        else:
            logger.success("✅ 笔记发布成功！")
            
    except Exception as e:
        logger.error(f"❌ 发布失败: {e}")
        raise

def main():
    """主函数"""
    # 测试参数
    test_topic = "春季护肤技巧"
    dry_run = True  # True=dry-run模式，False=真实发布
    
    logger.info("🎯 小红书自动发布 - 真实测试")
    logger.info(f"📍 测试主题: {test_topic}")
    logger.info(f"🔧 模式: {'Dry-run (测试)' if dry_run else '真实发布'}")
    logger.info("")
    
    # 执行测试
    test_publish_without_images(test_topic, dry_run=dry_run)
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("🎉 测试完成！")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()

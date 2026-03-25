#!/usr/bin/env python3
"""
基于合同示范文本库网站创建小红书内容
"""

from pathlib import Path
from loguru import logger
from content_generator import generate_note
from PIL import Image, ImageDraw, ImageFont
import json

def create_contract_library_content():
    """创建关于合同示范文本库的小红书内容"""
    
    # 根据网站信息构建主题
    topic = """国家市场监督管理总局推出的"合同示范文本库"，
    这是一个免费的公益平台，提供各类标准合同模板。
    包括旅游合同、服务合同、保管合同等8个部委合同和8个地方合同模板。
    网址：htsfwb.samr.gov.cn
    
    重点介绍：
    1. 2026年最新版：合同节水管理项目服务合同、研学旅游合同等
    2. 涵盖旅游、养老、家政、装修、健身等生活服务领域
    3. 免费下载，帮助保护消费者权益
    4. 可按年份、地区、分类筛选
    
    请生成一篇适合小红书的内容，标题吸引人，内容实用，
    帮助大家了解这个实用的政府资源，保护自己的合法权益。"""
    
    extra_requirements = """
    1. 标题要有吸引力，包含emoji
    2. 开头要引起共鸣（签合同时的困惑）
    3. 介绍这个文本库的价值
    4. 列举几个实用的合同类型
    5. 强调免费和权威性
    6. 结尾引导大家收藏
    7. 语气轻松友好，像朋友推荐
    """
    
    logger.info("🤖 使用DeepSeek生成小红书内容...")
    note = generate_note(topic, extra_requirements)
    
    return note

def create_info_graphics():
    """创建信息图片"""
    logger.info("🎨 创建信息图片...")
    
    output_dir = Path("output/contract_xhs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建3张信息图
    images = []
    
    # 图片1: 主标题图
    img1 = Image.new('RGB', (1080, 1080), color='#FFF5F5')
    draw1 = ImageDraw.Draw(img1)
    
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 70)
        subtitle_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 45)
        text_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 35)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
    
    # 绘制主标题
    title = "国家合同示范文本库"
    bbox = draw1.textbbox((0, 0), title, font=title_font)
    text_width = bbox[2] - bbox[0]
    draw1.text(((1080 - text_width) / 2, 200), title, fill='#FF6B9D', font=title_font)
    
    subtitle = "免费 · 权威 · 实用"
    bbox = draw1.textbbox((0, 0), subtitle, font=subtitle_font)
    text_width = bbox[2] - bbox[0]
    draw1.text(((1080 - text_width) / 2, 320), subtitle, fill='#666666', font=subtitle_font)
    
    # 添加图标/装饰元素
    draw1.ellipse([390, 450, 690, 750], fill='#FFE5E5', outline='#FF6B9D', width=5)
    icon_text = "📋"
    bbox = draw1.textbbox((0, 0), icon_text, font=title_font)
    text_width = bbox[2] - bbox[0]
    draw1.text(((1080 - text_width) / 2, 530), icon_text, font=title_font)
    
    url = "htsfwb.samr.gov.cn"
    bbox = draw1.textbbox((0, 0), url, font=text_font)
    text_width = bbox[2] - bbox[0]
    draw1.text(((1080 - text_width) / 2, 850), url, fill='#999999', font=text_font)
    
    img1_path = output_dir / "image1_title.jpg"
    img1.save(img1_path, quality=95)
    images.append(img1_path)
    logger.success(f"✅ 图片1已创建: {img1_path}")
    
    # 图片2: 合同类型列表
    img2 = Image.new('RGB', (1080, 1080), color='#F0F8FF')
    draw2 = ImageDraw.Draw(img2)
    
    list_title = "📝 部分合同类型"
    draw2.text((100, 100), list_title, fill='#2C3E50', font=subtitle_font)
    
    contracts = [
        "• 研学旅游合同",
        "• 境内/出境旅游合同",
        "• 养老机构服务合同",
        "• 家政服务合同",
        "• 装修施工合同",
        "• 体育健身服务合同",
        "• 预付式消费合同",
        "• 保管合同"
    ]
    
    y_position = 220
    for contract in contracts:
        draw2.text((120, y_position), contract, fill='#34495E', font=text_font)
        y_position += 90
    
    img2_path = output_dir / "image2_list.jpg"
    img2.save(img2_path, quality=95)
    images.append(img2_path)
    logger.success(f"✅ 图片2已创建: {img2_path}")
    
    # 图片3: 使用方法
    img3 = Image.new('RGB', (1080, 1080), color='#FFF9E6')
    draw3 = ImageDraw.Draw(img3)
    
    guide_title = "💡 使用方法"
    draw3.text((100, 100), guide_title, fill='#E67E22', font=subtitle_font)
    
    steps = [
        "1️⃣ 访问网站",
        "   htsfwb.samr.gov.cn",
        "",
        "2️⃣ 搜索或筛选",
        "   找到需要的合同类型",
        "",
        "3️⃣ 免费下载",
        "   Word/PDF格式",
        "",
        "4️⃣ 根据实际修改",
        "   保护自己权益"
    ]
    
    y_position = 220
    for step in steps:
        if step.startswith(('1️⃣', '2️⃣', '3️⃣', '4️⃣')):
            draw3.text((120, y_position), step, fill='#E67E22', font=text_font)
        else:
            draw3.text((120, y_position), step, fill='#7F8C8D', font=text_font)
        y_position += 65
    
    img3_path = output_dir / "image3_guide.jpg"
    img3.save(img3_path, quality=95)
    images.append(img3_path)
    logger.success(f"✅ 图片3已创建: {img3_path}")
    
    return images

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🚀 创建合同示范文本库小红书内容")
    logger.info("=" * 60)
    
    # 1. 生成文案
    note = create_contract_library_content()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("📄 生成的小红书内容:")
    logger.info("=" * 60)
    logger.info(f"标题: {note['title']}")
    logger.info("")
    logger.info(note['content'])
    logger.info("=" * 60)
    
    # 2. 创建图片
    logger.info("")
    image_paths = create_info_graphics()
    
    # 3. 保存结果
    result = {
        "title": note['title'],
        "content": note['content'],
        "tags": ["合同模板", "法律知识", "生活技巧", "权益保护"],
        "images": [str(p) for p in image_paths]
    }
    
    output_file = Path("output/contract_xhs/xhs_content.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    logger.success(f"💾 内容已保存: {output_file}")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ 内容创建完成！")
    logger.info("=" * 60)
    
    return result

if __name__ == "__main__":
    main()

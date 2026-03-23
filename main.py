"""
小红书自动发布工具 - 主入口
==============================
AI 生成文案 + AI 生成图片 + Playwright 自动发布

用法:
    1. 首次登录:        python main.py login
    2. 单篇发布:        python main.py publish --topic "秋天穿搭推荐"
    3. 试运行(不发布):   python main.py publish --topic "秋天穿搭推荐" --dry-run
    4. 批量发布:        python main.py batch --file topics.txt
    5. 用本地图片发布:   python main.py publish --topic "我的旅行" --images ./my_photos/
"""

import argparse
import json
import time
import hashlib
from pathlib import Path
from loguru import logger

from config import OUTPUT_DIR, PUBLISH_INTERVAL_SECONDS
from content_generator import generate_note
from image_generator import generate_images_for_note, use_local_images
from xhs_publisher import login_and_save_cookies, publish_note


def setup_logger():
    """配置日志"""
    log_file = OUTPUT_DIR / "publish.log"
    logger.add(
        str(log_file),
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )


def create_note_id(topic: str) -> str:
    """根据主题和时间戳创建唯一笔记 ID"""
    hash_str = hashlib.md5(f"{topic}{time.time()}".encode()).hexdigest()[:8]
    return f"note_{hash_str}"


def save_note_data(note_id: str, note: dict, image_paths: list):
    """保存笔记数据到本地（方便排查和重试）"""
    note_dir = OUTPUT_DIR / note_id
    note_dir.mkdir(parents=True, exist_ok=True)

    data = {
        **note,
        "image_paths": [str(p) for p in image_paths],
    }
    data_file = note_dir / "note_data.json"
    data_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"💾 笔记数据已保存: {data_file}")


def run_single_publish(topic: str, extra_req: str = "", dry_run: bool = False, local_images: str = ""):
    """
    执行单篇笔记的完整流程：生成文案 → 生成图片 → 发布

    Args:
        topic: 笔记主题
        extra_req: 额外要求
        dry_run: 试运行模式
        local_images: 本地图片目录（不走 AI 生图）
    """
    note_id = create_note_id(topic)

    # Step 1: 生成文案
    logger.info("=" * 50)
    logger.info(f"📝 Step 1: 生成文案 - 主题: {topic}")
    logger.info("=" * 50)
    note = generate_note(topic, extra_req)

    # Step 2: 生成/准备图片
    logger.info("=" * 50)
    logger.info("🎨 Step 2: 准备图片")
    logger.info("=" * 50)
    if local_images:
        image_paths = use_local_images(local_images)
    else:
        image_paths = generate_images_for_note(note["image_prompts"], note_id)

    if not image_paths:
        logger.error("❌ 没有可用图片，终止发布")
        return False

    # 保存笔记数据
    save_note_data(note_id, note, image_paths)

    # Step 3: 发布到小红书
    logger.info("=" * 50)
    logger.info("🚀 Step 3: 发布到小红书")
    logger.info("=" * 50)
    success = publish_note(
        title=note["title"],
        content=note["content"],
        tags=note["tags"],
        image_paths=image_paths,
        dry_run=dry_run,
    )

    if success:
        logger.success(f"🎉 笔记 [{note['title']}] 发布流程完成！")
    else:
        logger.error(f"💔 笔记 [{note['title']}] 发布失败")

    return success


def run_batch_publish(topics_file: str, dry_run: bool = False):
    """
    批量发布多篇笔记

    Args:
        topics_file: 主题列表文件路径（每行一个主题）
        dry_run: 试运行模式
    """
    topics_path = Path(topics_file)
    if not topics_path.exists():
        logger.error(f"❌ 主题文件不存在: {topics_file}")
        return

    topics = [
        line.strip()
        for line in topics_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

    logger.info(f"📋 共 {len(topics)} 个主题待发布")

    success_count = 0
    for i, topic in enumerate(topics, 1):
        logger.info(f"\n{'🔸' * 25}")
        logger.info(f"📌 发布第 {i}/{len(topics)} 篇: {topic}")
        logger.info(f"{'🔸' * 25}")

        success = run_single_publish(topic, dry_run=dry_run)
        if success:
            success_count += 1

        # 篇间间隔，避免被风控
        if i < len(topics):
            wait_time = PUBLISH_INTERVAL_SECONDS
            logger.info(f"⏰ 等待 {wait_time} 秒后发布下一篇...")
            time.sleep(wait_time)

    logger.info(f"\n📊 发布完成: 成功 {success_count}/{len(topics)} 篇")


def main():
    setup_logger()

    parser = argparse.ArgumentParser(
        description="🌟 小红书自动发布工具 - AI 生成文案 + 图片 + 自动发布",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # login 命令
    subparsers.add_parser("login", help="登录小红书并保存 Cookie")

    # publish 命令
    pub_parser = subparsers.add_parser("publish", help="发布单篇笔记")
    pub_parser.add_argument("--topic", required=True, help="笔记主题")
    pub_parser.add_argument("--extra", default="", help="额外要求")
    pub_parser.add_argument("--dry-run", action="store_true", help="试运行模式（不真正发布）")
    pub_parser.add_argument("--images", default="", help="使用本地图片目录（不走AI生图）")

    # batch 命令
    batch_parser = subparsers.add_parser("batch", help="批量发布笔记")
    batch_parser.add_argument("--file", required=True, help="主题列表文件路径")
    batch_parser.add_argument("--dry-run", action="store_true", help="试运行模式")

    args = parser.parse_args()

    if args.command == "login":
        login_and_save_cookies()

    elif args.command == "publish":
        run_single_publish(
            topic=args.topic,
            extra_req=args.extra,
            dry_run=args.dry_run,
            local_images=args.images,
        )

    elif args.command == "batch":
        run_batch_publish(
            topics_file=args.file,
            dry_run=args.dry_run,
        )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

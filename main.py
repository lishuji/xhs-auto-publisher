"""
小红书自动发布工具 - 主入口
==============================
AI 生成文案 + AI 生成图片 + Playwright 自动发布

优化版本：
- ✅ 自动重试机制（网络错误、API限流）
- ✅ 并发图片生成（3倍速度提升）
- ✅ 批量预生成优化（发布间隔期生成下一篇）

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
from concurrent.futures import ThreadPoolExecutor, Future

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


def run_batch_publish(topics_file: str, dry_run: bool = False, optimized: bool = True):
    """
    批量发布多篇笔记（支持优化模式）

    Args:
        topics_file: 主题列表文件路径（每行一个主题）
        dry_run: 试运行模式
        optimized: 是否启用优化模式（预生成下一篇内容）
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
    
    if optimized:
        logger.info("🚀 启用优化模式：发布间隔期预生成下一篇内容")
        _run_batch_publish_optimized(topics, dry_run)
    else:
        logger.info("⏱️  标准模式：逐篇生成并发布")
        _run_batch_publish_standard(topics, dry_run)


def _run_batch_publish_standard(topics: list[str], dry_run: bool):
    """标准批量发布（原有逻辑）"""
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


def _run_batch_publish_optimized(topics: list[str], dry_run: bool):
    """
    优化批量发布：发布间隔期预生成下一篇内容
    
    流程：
    1. 生成第1篇 -> 发布第1篇
    2. 等待间隔期间，同时生成第2篇
    3. 发布第2篇
    4. 等待间隔期间，同时生成第3篇
    ... 依此类推
    """
    success_count = 0
    prepared_contents = {}  # 缓存预生成的内容
    
    def prepare_content(topic: str) -> dict | None:
        """预生成内容（文案+图片）"""
        try:
            note_id = create_note_id(topic)
            logger.info(f"🔄 后台生成: {topic}")
            
            # 生成文案
            note = generate_note(topic)
            
            # 生成图片（并发模式）
            image_paths = generate_images_for_note(note["image_prompts"], note_id)
            
            if not image_paths:
                logger.warning(f"⚠️ 主题 '{topic}' 无可用图片")
                return None
            
            # 保存数据
            save_note_data(note_id, note, image_paths)
            
            return {
                "note_id": note_id,
                "note": note,
                "image_paths": image_paths,
            }
        except Exception as e:
            logger.error(f"❌ 预生成失败 '{topic}': {e}")
            return None
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        next_content_future: Future | None = None
        
        for i, topic in enumerate(topics, 1):
            logger.info(f"\n{'🔸' * 25}")
            logger.info(f"📌 发布第 {i}/{len(topics)} 篇: {topic}")
            logger.info(f"{'🔸' * 25}")
            
            # 获取内容（从缓存或现场生成）
            if topic in prepared_contents:
                logger.info("⚡ 使用预生成内容")
                content = prepared_contents.pop(topic)
            elif next_content_future and next_content_future.done():
                content = next_content_future.result()
                next_content_future = None
            else:
                logger.info("🔄 现场生成内容")
                content = prepare_content(topic)
            
            # 发布
            if content:
                success = publish_note(
                    title=content["note"]["title"],
                    content=content["note"]["content"],
                    tags=content["note"]["tags"],
                    image_paths=content["image_paths"],
                    dry_run=dry_run,
                )
                if success:
                    success_count += 1
                    logger.success(f"🎉 笔记 [{content['note']['title']}] 发布完成！")
                else:
                    logger.error(f"💔 笔记发布失败")
            else:
                logger.warning(f"⚠️ 跳过主题: {topic}")
            
            # 如果有下一篇，在等待期间预生成
            if i < len(topics):
                next_topic = topics[i]
                wait_time = PUBLISH_INTERVAL_SECONDS
                
                logger.info(f"⏰ 等待 {wait_time} 秒，同时生成下一篇...")
                
                # 启动异步生成任务
                next_content_future = executor.submit(prepare_content, next_topic)
                
                # 等待间隔时间
                time.sleep(wait_time)
                
                # 如果生成已完成，缓存结果
                if next_content_future.done():
                    result = next_content_future.result()
                    if result:
                        prepared_contents[next_topic] = result
                        logger.success(f"✅ 下一篇已准备就绪")
                    next_content_future = None
                else:
                    logger.info("⏳ 下一篇仍在生成中...")
    
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
    batch_parser.add_argument("--no-optimization", action="store_true", help="禁用优化模式（不预生成）")

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
            optimized=not args.no_optimization,
        )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

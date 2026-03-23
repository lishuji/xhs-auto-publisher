"""AI 图片生成模块 - 使用 OpenAI DALL·E 或兼容接口生成配图"""

import time
import httpx
from pathlib import Path
from openai import OpenAI
from loguru import logger
from config import OPENAI_API_KEY, OPENAI_BASE_URL, IMAGE_MODEL, OUTPUT_DIR


client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)


def generate_image(prompt: str, size: str = "1024x1024") -> str | None:
    """
    根据描述生成单张图片

    Args:
        prompt: 图片描述（英文）
        size: 图片尺寸

    Returns:
        str: 图片 URL，失败返回 None
    """
    try:
        logger.info(f"🎨 正在生成图片: {prompt[:60]}...")
        response = client.images.generate(
            model=IMAGE_MODEL,
            prompt=prompt,
            n=1,
            size=size,
            quality="standard",
        )
        url = response.data[0].url
        logger.success(f"✅ 图片生成成功")
        return url
    except Exception as e:
        logger.error(f"❌ 图片生成失败: {e}")
        return None


def download_image(url: str, save_path: Path) -> Path | None:
    """
    下载图片到本地

    Args:
        url: 图片 URL
        save_path: 保存路径

    Returns:
        Path: 保存的文件路径，失败返回 None
    """
    try:
        with httpx.Client(timeout=60) as http_client:
            resp = http_client.get(url)
            resp.raise_for_status()
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(resp.content)
            logger.info(f"📥 图片已保存: {save_path}")
            return save_path
    except Exception as e:
        logger.error(f"❌ 图片下载失败: {e}")
        return None


def generate_images_for_note(
    image_prompts: list[str],
    note_id: str = "default",
) -> list[Path]:
    """
    为一篇笔记生成所有配图并下载到本地

    Args:
        image_prompts: 图片描述列表（英文）
        note_id: 笔记标识，用于创建子目录

    Returns:
        list[Path]: 本地图片路径列表
    """
    image_dir = OUTPUT_DIR / note_id / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    local_paths = []
    for i, prompt in enumerate(image_prompts, 1):
        logger.info(f"🖼️  生成第 {i}/{len(image_prompts)} 张图片...")

        url = generate_image(prompt)
        if not url:
            logger.warning(f"⚠️ 跳过第 {i} 张图片")
            continue

        save_path = image_dir / f"image_{i}.png"
        local_path = download_image(url, save_path)
        if local_path:
            local_paths.append(local_path)

        # 避免 API 限流
        if i < len(image_prompts):
            time.sleep(2)

    logger.info(f"📸 共生成 {len(local_paths)}/{len(image_prompts)} 张图片")
    return local_paths


def use_local_images(image_dir: str | Path) -> list[Path]:
    """
    使用本地已有图片（备选方案，不走 AI 生图）

    Args:
        image_dir: 图片目录

    Returns:
        list[Path]: 图片路径列表
    """
    image_dir = Path(image_dir)
    extensions = {".jpg", ".jpeg", ".png", ".webp"}
    images = sorted(
        [f for f in image_dir.iterdir() if f.suffix.lower() in extensions]
    )
    logger.info(f"📂 找到 {len(images)} 张本地图片")
    return images


if __name__ == "__main__":
    # 测试图片生成
    prompts = [
        "A cozy autumn cafe scene with warm lighting, maple leaves visible through the window, a cup of hot latte on a wooden table, lifestyle photography style, high quality",
        "A beautiful autumn forest trail with golden and red leaves, sunlight filtering through trees, peaceful atmosphere, landscape photography, high quality",
    ]
    paths = generate_images_for_note(prompts, note_id="test")
    print(f"生成的图片: {paths}")

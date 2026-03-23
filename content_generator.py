"""AI 文案生成模块 - 使用 OpenAI 兼容接口生成小红书风格文案"""

import json
from openai import OpenAI
from loguru import logger
from config import OPENAI_API_KEY, OPENAI_BASE_URL, CHAT_MODEL


client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

SYSTEM_PROMPT = """你是一位专业的小红书内容创作者，擅长撰写吸引人的笔记。
你需要根据用户给出的主题，输出一篇完整的小红书笔记，格式要求：

1. 标题：15字以内，带1-2个emoji，吸引人点击
2. 正文：300-500字，分段落，语气轻松活泼，适当使用emoji
3. 话题标签：3-5个相关话题标签，格式如 #话题名称
4. 图片描述：为笔记生成3张配图的英文描述（用于AI生图），每个描述要具体、视觉化

请严格按以下 JSON 格式输出（不要包含```json标记）：
{
  "title": "笔记标题",
  "content": "笔记正文（包含emoji和换行）",
  "tags": ["话题1", "话题2", "话题3"],
  "image_prompts": [
    "English image description 1, high quality, lifestyle photography style",
    "English image description 2, high quality, lifestyle photography style",
    "English image description 3, high quality, lifestyle photography style"
  ]
}"""


def generate_note(topic: str, extra_requirements: str = "") -> dict:
    """
    根据主题生成小红书笔记内容

    Args:
        topic: 笔记主题
        extra_requirements: 额外要求（可选）

    Returns:
        dict: 包含 title, content, tags, image_prompts
    """
    user_message = f"主题：{topic}"
    if extra_requirements:
        user_message += f"\n额外要求：{extra_requirements}"

    logger.info(f"🤖 正在生成文案，主题: {topic}")

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.8,
            max_tokens=2000,
        )

        raw_text = response.choices[0].message.content.strip()

        # 清理可能的 markdown 代码块标记
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1]
        if raw_text.endswith("```"):
            raw_text = raw_text.rsplit("```", 1)[0]
        raw_text = raw_text.strip()

        note = json.loads(raw_text)

        # 校验必需字段
        required_keys = ["title", "content", "tags", "image_prompts"]
        for key in required_keys:
            if key not in note:
                raise ValueError(f"生成结果缺少字段: {key}")

        logger.success(f"✅ 文案生成成功: {note['title']}")
        return note

    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON 解析失败: {e}\n原始内容: {raw_text}")
        raise
    except Exception as e:
        logger.error(f"❌ 文案生成失败: {e}")
        raise


def generate_note_batch(topics: list[str]) -> list[dict]:
    """
    批量生成多篇笔记

    Args:
        topics: 主题列表

    Returns:
        list[dict]: 笔记内容列表
    """
    results = []
    for i, topic in enumerate(topics, 1):
        logger.info(f"📝 生成第 {i}/{len(topics)} 篇笔记...")
        try:
            note = generate_note(topic)
            results.append(note)
        except Exception as e:
            logger.warning(f"⚠️ 跳过主题 '{topic}': {e}")
            results.append(None)
    return results


if __name__ == "__main__":
    # 测试文案生成
    note = generate_note("秋天适合去哪里旅行", "推荐3个国内小众目的地")
    print(json.dumps(note, ensure_ascii=False, indent=2))

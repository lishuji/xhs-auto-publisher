"""测试API连接和配置"""

import sys
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_BASE_URL, CHAT_MODEL, IMAGE_MODEL

def test_api_config():
    """测试API配置"""
    print("=" * 60)
    print("🔍 检查API配置")
    print("=" * 60)
    
    print(f"\n配置信息:")
    print(f"  Base URL: {OPENAI_BASE_URL}")
    print(f"  Chat Model: {CHAT_MODEL}")
    print(f"  Image Model: {IMAGE_MODEL}")
    
    if OPENAI_API_KEY == "sk-your-api-key-here":
        print(f"  API Key: ⚠️  未配置（使用示例值）")
        print("\n❌ 请先配置真实的API Key")
        print("\n💡 配置步骤:")
        print("  1. 编辑 .env 文件")
        print("  2. 修改 OPENAI_API_KEY=your-real-key")
        print("  3. 保存文件后重新运行")
        return False
    else:
        print(f"  API Key: ✅ 已配置 ({OPENAI_API_KEY[:20]}...)")
    
    return True


def test_chat_api():
    """测试文案生成API"""
    print("\n" + "=" * 60)
    print("🤖 测试文案生成API (Chat)")
    print("=" * 60)
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        
        print("\n发送测试请求...")
        print(f"Model: {CHAT_MODEL}")
        print(f"Prompt: 你好，这是一个API连接测试")
        
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "user", "content": "你好，这是一个API连接测试，请回复：测试成功"}
            ],
            max_tokens=20,
            temperature=0.7
        )
        
        result = response.choices[0].message.content
        print(f"\n✅ API响应成功！")
        print(f"响应内容: {result}")
        print(f"用量统计: {response.usage.total_tokens} tokens")
        
        return True
        
    except Exception as e:
        print(f"\n❌ API调用失败: {e}")
        print("\n💡 可能的原因:")
        print("  1. API Key 不正确")
        print("  2. Base URL 不正确")
        print("  3. 账户余额不足")
        print("  4. 网络连接问题")
        print("  5. 模型名称不正确")
        
        if "Incorrect API key" in str(e):
            print("\n⚠️  检测到：API Key 错误")
        elif "Quota" in str(e) or "insufficient" in str(e):
            print("\n⚠️  检测到：配额不足或余额不足")
        elif "not found" in str(e):
            print("\n⚠️  检测到：模型不存在或Base URL错误")
        
        return False


def test_image_api():
    """测试图片生成API"""
    print("\n" + "=" * 60)
    print("🎨 测试图片生成API (DALL-E)")
    print("=" * 60)
    
    # 检查是否使用DeepSeek
    if "deepseek" in OPENAI_BASE_URL.lower():
        print("\n⚠️  DeepSeek 不支持图片生成")
        print("💡 建议:")
        print("  1. 使用 OpenAI 官方 API")
        print("  2. 或使用本地图片: --images ./test_images/")
        return None
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        
        print("\n发送测试请求...")
        print(f"Model: {IMAGE_MODEL}")
        print(f"Prompt: A simple test image")
        print(f"⚠️  这会消耗约 $0.04")
        
        # 询问用户是否继续
        response = input("\n是否继续图片生成测试？(y/N): ")
        if response.lower() != 'y':
            print("跳过图片生成测试")
            return None
        
        response = client.images.generate(
            model=IMAGE_MODEL,
            prompt="A simple test image, minimalist style",
            n=1,
            size="1024x1024",
            quality="standard"
        )
        
        url = response.data[0].url
        print(f"\n✅ 图片生成成功！")
        print(f"图片URL: {url[:60]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 图片生成失败: {e}")
        print("\n💡 可能的原因:")
        print("  1. API Key 不正确")
        print("  2. 不支持图片生成（如DeepSeek）")
        print("  3. 账户余额不足")
        print("  4. 内容策略违规")
        
        return False


def show_next_steps(chat_ok, image_ok):
    """显示下一步操作"""
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    print("\n结果:")
    print(f"  文案生成API: {'✅ 正常' if chat_ok else '❌ 失败'}")
    
    if image_ok is None:
        print(f"  图片生成API: ⚠️  跳过")
    else:
        print(f"  图片生成API: {'✅ 正常' if image_ok else '❌ 失败'}")
    
    print("\n" + "=" * 60)
    
    if chat_ok:
        print("✅ API配置正常，可以开始测试！")
        print("\n💡 下一步:")
        print("  1. 登录小红书:")
        print("     python main.py login")
        print()
        print("  2. Dry-Run测试 (不真实发布):")
        
        if image_ok:
            print("     python main.py publish --topic \"测试主题\" --dry-run")
        else:
            print("     python main.py publish --topic \"测试主题\" --images ./test_images/ --dry-run")
            print("     (使用本地图片，因为图片API不可用)")
        
        print()
        print("  3. 查看详细测试指南:")
        print("     cat 配置和测试指南.md")
    else:
        print("❌ API配置有问题，请先解决上述问题")
        print("\n💡 配置帮助:")
        print("  1. 查看配置指南: cat 配置和测试指南.md")
        print("  2. 编辑配置: vim .env")
        print("  3. 重新测试: python test_api_connection.py")
    
    print("=" * 60)


def main():
    """主函数"""
    print("🚀 小红书自动发布工具 - API连接测试")
    print("=" * 60)
    print("本测试将验证API配置是否正确")
    print("=" * 60)
    
    # 测试配置
    config_ok = test_api_config()
    if not config_ok:
        sys.exit(1)
    
    # 测试Chat API
    chat_ok = test_chat_api()
    
    # 测试Image API
    image_ok = test_image_api()
    
    # 显示下一步
    show_next_steps(chat_ok, image_ok)
    
    sys.exit(0 if chat_ok else 1)


if __name__ == "__main__":
    main()

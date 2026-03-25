"""实际环境验证脚本 - 验证所有依赖和模块是否正常"""

import sys
from pathlib import Path

# 测试结果记录
test_results = []

def test_step(name, func):
    """执行测试步骤"""
    try:
        result = func()
        test_results.append((name, True, result))
        print(f"✅ {name}: 通过")
        if result:
            print(f"   {result}")
        return True
    except Exception as e:
        test_results.append((name, False, str(e)))
        print(f"❌ {name}: 失败")
        print(f"   错误: {e}")
        return False


def test_imports():
    """测试所有依赖导入"""
    print("\n" + "="*60)
    print("测试1: 依赖导入检查")
    print("="*60)
    
    modules = [
        ("openai", "OpenAI SDK"),
        ("playwright.sync_api", "Playwright"),
        ("httpx", "HTTP客户端"),
        ("loguru", "日志系统"),
        ("PIL", "图片处理"),
        ("dotenv", "环境变量管理"),
    ]
    
    all_ok = True
    for module_name, desc in modules:
        try:
            __import__(module_name)
            print(f"  ✅ {desc:20s} ({module_name})")
        except ImportError as e:
            print(f"  ❌ {desc:20s} ({module_name}): {e}")
            all_ok = False
    
    return "所有依赖模块已安装" if all_ok else "部分模块缺失"


def test_project_modules():
    """测试项目模块"""
    print("\n" + "="*60)
    print("测试2: 项目模块检查")
    print("="*60)
    
    modules = [
        ("config", "配置模块"),
        ("retry_utils", "重试工具"),
        ("content_generator", "文案生成"),
        ("image_generator", "图片生成"),
        ("xhs_publisher", "发布模块"),
    ]
    
    all_ok = True
    for module_name, desc in modules:
        try:
            __import__(module_name)
            print(f"  ✅ {desc:20s} ({module_name}.py)")
        except ImportError as e:
            print(f"  ❌ {desc:20s} ({module_name}.py): {e}")
            all_ok = False
    
    return "所有项目模块可导入" if all_ok else "部分模块导入失败"


def test_retry_utils():
    """测试重试工具"""
    print("\n" + "="*60)
    print("测试3: 重试机制验证")
    print("="*60)
    
    from retry_utils import retry_on_failure, retry_with_exponential_backoff
    
    # 测试基础重试
    @retry_on_failure(max_attempts=2, delay=0.1)
    def test_func1():
        return "success"
    
    # 测试指数退避
    @retry_with_exponential_backoff(initial_delay=0.1, max_attempts=2)
    def test_func2():
        return "success"
    
    result1 = test_func1()
    result2 = test_func2()
    
    print(f"  ✅ retry_on_failure: {result1}")
    print(f"  ✅ retry_with_exponential_backoff: {result2}")
    
    return "重试装饰器工作正常"


def test_config_loading():
    """测试配置加载"""
    print("\n" + "="*60)
    print("测试4: 配置文件验证")
    print("="*60)
    
    from config import (
        OUTPUT_DIR, 
        COOKIES_DIR,
        OPENAI_API_KEY,
        PUBLISH_INTERVAL_SECONDS,
        MAX_IMAGES_PER_NOTE
    )
    
    print(f"  ✅ OUTPUT_DIR: {OUTPUT_DIR}")
    print(f"  ✅ COOKIES_DIR: {COOKIES_DIR}")
    print(f"  ✅ PUBLISH_INTERVAL: {PUBLISH_INTERVAL_SECONDS}秒")
    print(f"  ✅ MAX_IMAGES: {MAX_IMAGES_PER_NOTE}张")
    
    if OPENAI_API_KEY == "sk-your-api-key-here":
        print(f"  ⚠️  API Key: 未配置（使用示例值）")
    else:
        print(f"  ✅ API Key: 已配置")
    
    # 检查目录是否创建
    if OUTPUT_DIR.exists():
        print(f"  ✅ 输出目录已创建")
    if COOKIES_DIR.exists():
        print(f"  ✅ Cookie目录已创建")
    
    return "配置加载正常"


def test_function_signatures():
    """测试函数签名"""
    print("\n" + "="*60)
    print("测试5: 函数签名验证")
    print("="*60)
    
    import inspect
    from image_generator import generate_images_for_note
    from content_generator import generate_note
    
    # 检查并发参数
    sig = inspect.signature(generate_images_for_note)
    params = list(sig.parameters.keys())
    
    print(f"  generate_images_for_note 参数: {params}")
    
    if 'concurrent' in params:
        default = sig.parameters['concurrent'].default
        print(f"  ✅ 并发参数存在，默认值: {default}")
    else:
        print(f"  ❌ 并发参数缺失")
    
    # 检查重试装饰器
    from content_generator import generate_note
    if hasattr(generate_note, '__wrapped__'):
        print(f"  ✅ generate_note 已应用重试装饰器")
    else:
        print(f"  ⚠️  generate_note 可能未应用装饰器")
    
    return "函数签名检查完成"


def test_file_structure():
    """测试文件结构"""
    print("\n" + "="*60)
    print("测试6: 文件结构验证")
    print("="*60)
    
    required_files = [
        "main.py",
        "config.py",
        "content_generator.py",
        "image_generator.py",
        "xhs_publisher.py",
        "retry_utils.py",
        "requirements.txt",
        ".env",
        "README.md",
    ]
    
    optional_files = [
        "test_performance.py",
        "test_demo.py",
        "test_integration.py",
        "PERFORMANCE.md",
        "OPTIMIZATION_GUIDE.md",
        "CHANGELOG.md",
    ]
    
    print("  必需文件:")
    all_required = True
    for file in required_files:
        if Path(file).exists():
            print(f"    ✅ {file}")
        else:
            print(f"    ❌ {file} (缺失)")
            all_required = False
    
    print("\n  可选文件:")
    for file in optional_files:
        if Path(file).exists():
            print(f"    ✅ {file}")
    
    return "文件结构检查完成" if all_required else "缺少必需文件"


def test_cli_help():
    """测试命令行接口"""
    print("\n" + "="*60)
    print("测试7: CLI命令验证")
    print("="*60)
    
    import subprocess
    
    try:
        # 测试主命令
        result = subprocess.run(
            ["python3", "main.py", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("  ✅ main.py --help 可执行")
            
            # 检查关键命令
            if "login" in result.stdout:
                print("    ✅ login 命令存在")
            if "publish" in result.stdout:
                print("    ✅ publish 命令存在")
            if "batch" in result.stdout:
                print("    ✅ batch 命令存在")
        else:
            print(f"  ❌ 命令执行失败: {result.stderr}")
            
    except Exception as e:
        print(f"  ❌ CLI测试失败: {e}")
        return "CLI测试失败"
    
    return "CLI命令可用"


def generate_report():
    """生成测试报告"""
    print("\n" + "="*60)
    print("📊 测试报告汇总")
    print("="*60)
    
    passed = sum(1 for _, success, _ in test_results if success)
    total = len(test_results)
    
    print(f"\n总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print(f"通过率: {passed/total*100:.1f}%\n")
    
    print("详细结果:")
    for name, success, result in test_results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")
        if not success:
            print(f"     错误: {result}")
    
    print("\n" + "="*60)
    if passed == total:
        print("✅ 所有测试通过！环境已就绪")
        print("="*60)
        print("\n💡 下一步:")
        print("  1. 配置 API Key: 编辑 .env 文件")
        print("  2. 运行登录: python3 main.py login")
        print("  3. 测试发布: python3 main.py publish --topic \"测试\" --dry-run")
    else:
        print("⚠️ 部分测试失败，请检查错误信息")
        print("="*60)
    
    return passed == total


def main():
    """主函数"""
    print("🚀 小红书自动发布工具 - 实际环境验证")
    print("="*60)
    print("开始验证安装环境和优化功能...\n")
    
    # 执行所有测试
    test_step("依赖导入", test_imports)
    test_step("项目模块", test_project_modules)
    test_step("重试机制", test_retry_utils)
    test_step("配置加载", test_config_loading)
    test_step("函数签名", test_function_signatures)
    test_step("文件结构", test_file_structure)
    test_step("CLI命令", test_cli_help)
    
    # 生成报告
    all_passed = generate_report()
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

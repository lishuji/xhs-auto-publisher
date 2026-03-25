"""性能优化测试脚本 - 验证重试机制和并发优化"""

import time
import sys
from pathlib import Path

# 简单的日志函数（不依赖loguru）
class SimpleLogger:
    @staticmethod
    def info(msg):
        print(f"[INFO] {msg}")
    
    @staticmethod
    def success(msg):
        print(f"[SUCCESS] {msg}")
    
    @staticmethod
    def error(msg):
        print(f"[ERROR] {msg}")
    
    @staticmethod
    def warning(msg):
        print(f"[WARNING] {msg}")

logger = SimpleLogger()

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from retry_utils import retry_on_failure, retry_with_exponential_backoff


def test_retry_mechanism():
    """测试重试机制"""
    logger.info("=" * 60)
    logger.info("测试1: 基础重试机制")
    logger.info("=" * 60)
    
    # 模拟失败2次后成功的场景
    @retry_on_failure(max_attempts=3, delay=0.5, backoff=1.5)
    def flaky_function():
        if not hasattr(flaky_function, "call_count"):
            flaky_function.call_count = 0
        flaky_function.call_count += 1
        
        if flaky_function.call_count < 3:
            logger.info(f"第 {flaky_function.call_count} 次调用：模拟失败")
            raise ConnectionError("模拟网络错误")
        
        logger.info(f"第 {flaky_function.call_count} 次调用：成功")
        return "成功"
    
    try:
        start = time.time()
        result = flaky_function()
        elapsed = time.time() - start
        logger.success(f"✅ 测试通过！结果: {result}, 耗时: {elapsed:.1f}秒")
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")


def test_exponential_backoff():
    """测试指数退避重试"""
    logger.info("\n" + "=" * 60)
    logger.info("测试2: 指数退避重试")
    logger.info("=" * 60)
    
    @retry_with_exponential_backoff(initial_delay=0.5, max_attempts=4, exponential_base=2)
    def rate_limited_function():
        if not hasattr(rate_limited_function, "call_count"):
            rate_limited_function.call_count = 0
        rate_limited_function.call_count += 1
        
        if rate_limited_function.call_count < 4:
            logger.info(f"第 {rate_limited_function.call_count} 次调用：模拟API限流")
            raise Exception("429 Too Many Requests")
        
        logger.info(f"第 {rate_limited_function.call_count} 次调用：成功")
        return "成功"
    
    try:
        start = time.time()
        result = rate_limited_function()
        elapsed = time.time() - start
        logger.success(f"✅ 测试通过！结果: {result}, 耗时: {elapsed:.1f}秒")
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")


def test_concurrent_vs_sequential():
    """测试并发 vs 串行性能"""
    logger.info("\n" + "=" * 60)
    logger.info("测试3: 并发性能对比")
    logger.info("=" * 60)
    
    from concurrent.futures import ThreadPoolExecutor
    import random
    
    def simulate_image_generation(index: int) -> float:
        """模拟图片生成（0.5-1秒随机延迟）"""
        delay = random.uniform(0.5, 1.0)
        time.sleep(delay)
        return delay
    
    # 串行执行
    logger.info("📌 串行执行3次图片生成...")
    start_sequential = time.time()
    sequential_times = []
    for i in range(3):
        t = simulate_image_generation(i)
        sequential_times.append(t)
    sequential_total = time.time() - start_sequential
    
    logger.info(f"串行耗时: {sequential_total:.2f}秒 (单次: {sequential_times})")
    
    # 并发执行
    logger.info("\n📌 并发执行3次图片生成...")
    start_concurrent = time.time()
    concurrent_times = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(simulate_image_generation, i) for i in range(3)]
        concurrent_times = [f.result() for f in futures]
    concurrent_total = time.time() - start_concurrent
    
    logger.info(f"并发耗时: {concurrent_total:.2f}秒 (单次: {concurrent_times})")
    
    # 性能对比
    speedup = sequential_total / concurrent_total
    logger.success(f"\n⚡ 性能提升: {speedup:.2f}x (节省 {sequential_total - concurrent_total:.2f}秒)")


def test_batch_optimization_simulation():
    """模拟批量发布优化效果"""
    logger.info("\n" + "=" * 60)
    logger.info("测试4: 批量发布优化模拟")
    logger.info("=" * 60)
    
    def simulate_generate_content():
        """模拟内容生成（2秒）"""
        time.sleep(0.2)  # 缩短到0.2秒用于测试
        return {"title": "测试", "content": "测试内容"}
    
    def simulate_publish():
        """模拟发布（0.5秒）"""
        time.sleep(0.05)
    
    INTERVAL = 0.5  # 模拟间隔（缩短到0.5秒）
    NUM_POSTS = 5
    
    # 标准模式
    logger.info("📌 标准模式：逐篇生成发布...")
    start_standard = time.time()
    for i in range(NUM_POSTS):
        simulate_generate_content()
        simulate_publish()
        if i < NUM_POSTS - 1:
            time.sleep(INTERVAL)
    standard_total = time.time() - start_standard
    logger.info(f"标准模式耗时: {standard_total:.2f}秒")
    
    # 优化模式（模拟预生成）
    logger.info("\n📌 优化模式：间隔期预生成...")
    start_optimized = time.time()
    from concurrent.futures import ThreadPoolExecutor, Future
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        next_content_future: Future | None = None
        
        for i in range(NUM_POSTS):
            # 获取内容
            if next_content_future and next_content_future.done():
                content = next_content_future.result()
                next_content_future = None
            else:
                content = simulate_generate_content()
            
            # 发布
            simulate_publish()
            
            # 如果有下一篇，在间隔期预生成
            if i < NUM_POSTS - 1:
                next_content_future = executor.submit(simulate_generate_content)
                time.sleep(INTERVAL)
    
    optimized_total = time.time() - start_optimized
    logger.info(f"优化模式耗时: {optimized_total:.2f}秒")
    
    # 性能对比
    saved = standard_total - optimized_total
    improvement = (saved / standard_total) * 100
    logger.success(f"\n⚡ 优化效果: 节省 {saved:.2f}秒 ({improvement:.1f}%)")


def main():
    """运行所有测试"""
    logger.info("🚀 开始性能优化测试\n")
    
    test_retry_mechanism()
    test_exponential_backoff()
    test_concurrent_vs_sequential()
    test_batch_optimization_simulation()
    
    logger.info("\n" + "=" * 60)
    logger.success("✅ 所有测试完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

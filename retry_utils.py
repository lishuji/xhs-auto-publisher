"""重试机制工具模块 - 为API调用提供自动重试功能"""

import time
import functools
from typing import Callable, Type, Tuple

# 简单的日志函数（避免循环依赖）
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

try:
    from loguru import logger
except ImportError:
    logger = SimpleLogger()


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 2.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable[[Exception, int], None] | None = None,
):
    """
    装饰器：为函数添加自动重试机制
    
    Args:
        max_attempts: 最大尝试次数（包括首次）
        delay: 初始重试延迟（秒）
        backoff: 延迟倍数（每次重试延迟时间翻倍）
        exceptions: 需要重试的异常类型元组
        on_retry: 重试时的回调函数 (exception, attempt_number) -> None
    
    Returns:
        装饰后的函数
    
    Example:
        @retry_on_failure(max_attempts=3, delay=1, backoff=2)
        def api_call():
            # 可能失败的 API 调用
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 1:
                        logger.success(f"✅ 第 {attempt} 次尝试成功")
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(f"❌ 已达最大重试次数 ({max_attempts})，最终失败")
                        raise
                    
                    # 执行重试回调
                    if on_retry:
                        on_retry(e, attempt)
                    else:
                        logger.warning(
                            f"⚠️ 第 {attempt} 次尝试失败: {e}, "
                            f"将在 {current_delay:.1f} 秒后重试..."
                        )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception
        
        return wrapper
    return decorator


def retry_with_exponential_backoff(
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    max_attempts: int = 5,
):
    """
    装饰器：使用指数退避策略的重试机制（适用于 API 限流场景）
    
    Args:
        initial_delay: 初始延迟（秒）
        max_delay: 最大延迟（秒）
        exponential_base: 指数基数
        max_attempts: 最大尝试次数
    
    Example:
        @retry_with_exponential_backoff(initial_delay=2, max_attempts=5)
        def rate_limited_api_call():
            # 可能被限流的 API 调用
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 1:
                        logger.success(f"✅ 第 {attempt} 次尝试成功")
                    return result
                    
                except Exception as e:
                    if attempt == max_attempts:
                        logger.error(f"❌ 已达最大重试次数 ({max_attempts})，最终失败: {e}")
                        raise
                    
                    # 计算延迟时间（指数退避 + 随机抖动）
                    delay = min(
                        initial_delay * (exponential_base ** (attempt - 1)),
                        max_delay
                    )
                    
                    logger.warning(
                        f"⚠️ 第 {attempt} 次尝试失败: {e}, "
                        f"将在 {delay:.1f} 秒后重试..."
                    )
                    
                    time.sleep(delay)
            
        return wrapper
    return decorator


class RetryableError(Exception):
    """可重试的错误（用于业务逻辑中明确标识可重试的场景）"""
    pass


if __name__ == "__main__":
    # 测试重试机制
    
    @retry_on_failure(max_attempts=3, delay=1, backoff=2)
    def test_function_success_on_second_try():
        """测试：第2次尝试成功"""
        if not hasattr(test_function_success_on_second_try, "call_count"):
            test_function_success_on_second_try.call_count = 0
        test_function_success_on_second_try.call_count += 1
        
        if test_function_success_on_second_try.call_count < 2:
            raise ConnectionError("模拟网络错误")
        return "成功"
    
    
    @retry_with_exponential_backoff(initial_delay=0.5, max_attempts=3)
    def test_exponential_backoff():
        """测试：指数退避"""
        if not hasattr(test_exponential_backoff, "call_count"):
            test_exponential_backoff.call_count = 0
        test_exponential_backoff.call_count += 1
        
        if test_exponential_backoff.call_count < 3:
            raise Exception(f"第 {test_exponential_backoff.call_count} 次失败")
        return "成功"
    
    
    # 运行测试
    print("测试1: 基础重试机制")
    result1 = test_function_success_on_second_try()
    print(f"结果: {result1}\n")
    
    print("测试2: 指数退避")
    result2 = test_exponential_backoff()
    print(f"结果: {result2}")

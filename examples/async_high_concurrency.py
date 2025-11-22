# async_high_concurrency.py
# 目标：演示如何使用 AsyncThordataClient 实现高并发请求

import os
import asyncio
import aiohttp
from thordata_sdk import AsyncThordataClient 

# --- 配置 ---
# 警告：不要将密码硬编码在最终提交中！这里仅用于示例。
THORDATA_USER = os.getenv("THORDATA_USER", "thordata-test-user") 
THORDATA_PASS = os.getenv("THORDATA_PASS", "test-password")

# 并发目标 URLs
# 目标：同时请求 5 个不同的 IP 测试端点
TARGET_URLS = [
    "http://httpbin.org/ip",
    "http://httpbin.org/ip",
    "http://httpbin.org/ip",
    "http://httpbin.org/ip",
    "http://httpbin.org/ip",
]

async def fetch_url(client: AsyncThordataClient, url: str, index: int):
    """异步请求单个 URL 并处理响应"""
    try:
        # 使用 async with 语法自动管理 ClientSession
        # 传递 headers 用于标识请求，方便调试
        async with client.get(url, headers={'X-Request-Index': str(index)}) as response:
            # 读取响应内容
            data = await response.json()
            # 验证状态码
            response.raise_for_status()
            
            # 打印结果
            print(f"[Request {index}] ✅ Success: IP is {data.get('origin')}, Status: {response.status}")
            return f"Request {index} successful"

    except aiohttp.ClientError as e:
        print(f"[Request {index}] ❌ Failure (ClientError): {e}")
        return f"Request {index} failed"
    except Exception as e:
        print(f"[Request {index}] ❌ Failure (General): {e}")
        return f"Request {index} failed"

async def run_async_test():
    """主异步函数，创建并发任务"""
    print("--- 1. 初始化 AsyncThordata 客户端 ---")
    
    # 使用 async with 确保 ClientSession 在任务完成后关闭
    async with AsyncThordataClient(auth_user=THORDATA_USER, auth_pass=THORDATA_PASS) as client:
        print("--- 2. 创建高并发任务（同时请求 5 个 URL） ---")
        
        # 创建多个任务 (coroutines)，这里的关键是 list comprehension
        tasks = [fetch_url(client, url, i) for i, url in enumerate(TARGET_URLS)]
        
        # 并发运行所有任务，等待它们全部完成
        results = await asyncio.gather(*tasks)
        
        print("\n--- 3. 结果汇总 ---")
        print(f"总请求数: {len(results)}")
        print(f"成功/失败详情已在上方打印。")

if __name__ == "__main__":
    print("--- Thordata SDK 异步高并发测试脚本 ---")
    
    if THORDATA_USER == "thordata-test-user":
        print("💡 提示：你正在使用示例占位符账户。请替换为你的真实认证信息来运行。")
        
    # 运行主异步函数
    asyncio.run(run_async_test())
    print("---------------------------------")
# examples/test_new_features.py
import os
import asyncio
import logging
from dotenv import load_dotenv # 如果没有这个库，就 pip install python-dotenv

# 关键：导入我们新加的枚举！
from thordata_sdk import ThordataClient, AsyncThordataClient, Engine, GoogleSearchType

# 设置日志级别为 INFO，这样能看到 SDK 内部打印的请求信息
logging.basicConfig(level=logging.INFO)

# 加载环境变量 (或者你可以直接把 Token 写死在这里测试)
load_dotenv()
SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN") or "fb6b478700dbbdf3651f314dde1e673a"
PUBLIC_TOKEN = os.getenv("THORDATA_PUBLIC_TOKEN") or "eWEiAXxMfB05VQEAYXcLRgVYbQ18HjBTeGUkSgRZAGpWUnpmWVMLZ1JZB1g+BQ4tPQhIWzkP"
PUBLIC_KEY = os.getenv("THORDATA_PUBLIC_KEY") or "3ndjtera"

def test_sync_features():
    print("\n--- 🧪 开始测试: 同步客户端 (Sync) ---")
    client = ThordataClient(SCRAPER_TOKEN, PUBLIC_TOKEN, PUBLIC_KEY)

    # 测试 1: 使用枚举 (Engine.BING)
    print("\n[1] 测试枚举传参 (Bing)...")
    try:
        # 注意：这里 IDE 应该会提示 Engine.BING
        results = client.serp_search("Thordata SDK", engine=Engine.BING)
        print(f"✅ Bing 搜索成功! 收到 {len(results)} 条结果")
    except Exception as e:
        print(f"❌ Bing 测试失败: {e}")

    # 测试 2: 参数透传 (**kwargs) - 测试 Google Shopping
    print("\n[2] 测试高级参数透传 (Google Shopping)...")
    try:
        # 我们没有在 SDK 里定义 'type' 参数，但通过 **kwargs 应该能传进去
        # 这里同时也用了 GoogleSearchType 枚举
        results = client.serp_search(
            "iPhone 15", 
            engine=Engine.GOOGLE, 
            type=GoogleSearchType.SHOPPING, # 或者直接写字符串 "shopping"
            location="United States"       # 额外参数
        )
        # 简单的验证：如果是购物搜索，结果结构通常不一样，或者我们看日志
        print(f"✅ Google Shopping 搜索成功!")
    except Exception as e:
        print(f"❌ Google Shopping 测试失败: {e}")

async def test_async_features():
    print("\n--- 🧪 开始测试: 异步客户端 (Async) ---")
    async with AsyncThordataClient(SCRAPER_TOKEN, PUBLIC_TOKEN, PUBLIC_KEY) as client:
        
        # 测试 3: 异步 + Yandex (逻辑最复杂的那个)
        print("\n[3] 测试异步 Yandex (检查 parameters.py 逻辑)...")
        try:
            results = await client.serp_search("Python Async", engine=Engine.YANDEX)
            # 增加这一行检查：
            if "organic" in results or "search_metadata" in results:
                 print(f"✅ Yandex 异步搜索成功! (元数据: {results.get('search_metadata', {}).get('status')})")
            else:
                 print(f"⚠️ Yandex 返回了 200，但内容似乎为空: {results}")
        except Exception as e:
            print(f"❌ Yandex 测试失败: {e}")

if __name__ == "__main__":
    # 运行同步测试
    test_sync_features()
    
    # 运行异步测试
    asyncio.run(test_async_features())
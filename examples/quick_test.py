# quick_test.py
# 目标：演示如何使用 ThordataClient 通过代理请求并验证 IP 地址

import os
import requests
from thordata_sdk.client import ThordataClient # 导入我们刚写的客户端类

# --- 配置 ---
# 警告：不要将密码硬编码在最终提交中！这里仅用于示例。
# 建议通过环境变量获取认证信息
THORDATA_USER = os.getenv("THORDATA_USER", "thordata-test-user") 
THORDATA_PASS = os.getenv("THORDATA_PASS", "test-password")

# 目标 URL：httpbin.org/ip 会返回请求的源 IP 地址
TARGET_URL = "http://httpbin.org/ip" 

def run_quick_test():
    """
    初始化客户端并发送请求，打印代理后的 IP 地址。
    """
    print("--- 1. 初始化 Thordata 客户端 ---")
    try:
        # 使用你实际的用户名和密码
        client = ThordataClient(auth_user=THORDATA_USER, auth_pass=THORDATA_PASS)
        
        print(f"--- 2. 通过 Thordata 代理请求: {TARGET_URL} ---")
        response = client.get(TARGET_URL, timeout=15)

        if response.status_code == 200:
            data = response.json()
            print("✅ 成功！请求通过代理发送。")
            print(f"返回的源 IP 地址 (Origin IP): {data.get('origin')}")
            print(f"Status Code: {response.status_code}")
        else:
            print(f"❌ 失败！请求状态码: {response.status_code}")
            
    except requests.RequestException as e:
        print(f"❌ 请求发生错误 (连接或超时): {e}")
    except Exception as e:
        print(f"❌ 发生意外错误: {e}")

if __name__ == "__main__":
    print("--- Thordata SDK 快速测试脚本 ---")
    
    if THORDATA_USER == "thordata-test-user":
        print("💡 提示：你正在使用示例占位符账户。请替换为你的真实认证信息来运行。")
        
    run_quick_test()
    print("---------------------------------")
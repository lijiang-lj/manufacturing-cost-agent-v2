# -*- coding: utf-8 -*-
"""
以 LangChain 的 AzureChatOpenAI 调用格式测试 Azure OpenAI 连接
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

# -------------------------------------------------------------------
# 1) 加载 .env（优先项目根目录）
# -------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent
env_path = ROOT_DIR / ".env"

if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ 已加载环境文件: {env_path}")
else:
    print("⚠️ 未在项目根目录找到 .env，将直接使用系统环境变量。")

# -------------------------------------------------------------------
# 2) 读取必须的环境变量
# -------------------------------------------------------------------
required_vars = [
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_DEPLOYMENT",
    "AZURE_OPENAI_API_VERSION",
]

missing = [k for k in required_vars if not os.getenv(k)]
if missing:
    print("\n❌ 缺少以下环境变量，请在 .env 或系统环境中补全：")
    for k in missing:
        print(f"   - {k}")
    raise SystemExit(1)

endpoint    = os.environ["AZURE_OPENAI_ENDPOINT"]
api_key     = os.environ["AZURE_OPENAI_API_KEY"]
deployment  = os.environ["AZURE_OPENAI_DEPLOYMENT"]
api_version = os.environ["AZURE_OPENAI_API_VERSION"]

print("\n🔧 当前配置：")
print(f"   AZURE_OPENAI_ENDPOINT   = {endpoint}")
print(f"   AZURE_OPENAI_DEPLOYMENT = {deployment}")
print(f"   AZURE_OPENAI_API_VERSION= {api_version}")

# -------------------------------------------------------------------
# 3) 可选：配置代理（仅当 .env / 环境变量提供时才生效）
#    支持 PROXY_URL / HTTPS_PROXY / HTTP_PROXY 三选一；无需就不设置
# -------------------------------------------------------------------
proxy = os.getenv("PROXY_URL") or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
no_proxy = os.getenv("NO_PROXY")
if proxy:
    os.environ["HTTP_PROXY"]  = proxy
    os.environ["HTTPS_PROXY"] = proxy
if no_proxy:
    os.environ["NO_PROXY"] = no_proxy
print(f"\n🌐 Proxy configured: {'YES' if proxy else 'NO'}")

# -------------------------------------------------------------------
# 4) 用 AzureChatOpenAI 初始化，发起一次简单请求
# -------------------------------------------------------------------
print("\n🚀 正在尝试连接 Azure OpenAI...")

llm = AzureChatOpenAI(
    deployment_name=deployment,          # ✅ 用部署名
    api_key=api_key,
    azure_endpoint=endpoint,
    api_version=api_version,
    temperature=1.0,
)

try:
    # 与你之前“能跑”的格式一致：直接 invoke
    response = llm.invoke("Say hello from Azure GPT-5.")
    print("\n✅ 调用成功！返回内容示例：")
    print("-" * 60)
    print(response.content)
    print("-" * 60)

    # 兼容地输出一些可选调试信息
    model_info = getattr(llm, "model_name", deployment)
    print("\n📊 调试信息：")
    print(f"   model/deployment: {model_info}")
    print(f"   endpoint:         {endpoint}")
    print(f"   api_version:      {api_version}")

except Exception as e:
    print("\n❌ 调用 Azure OpenAI 失败：")
    print(f"   {type(e).__name__}: {e}")
    print("\n请检查：")
    print("  1. endpoint 是否正确（https://<资源名>.openai.azure.com/）")
    print("  2. api_key 是否对应该资源")
    print("  3. deployment 名称是否和 Azure 门户中的部署名称一致")
    print("  4. api_version 是否为该部署支持的版本")
    print("  5. 公司网络 / 代理是否允许访问 *.openai.azure.com")
    raise

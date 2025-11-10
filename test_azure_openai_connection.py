import os
from pathlib import Path

from dotenv import load_dotenv

try:
    from openai import AzureOpenAI
except ImportError:
    print("❌ 未找到 openai 包，请先安装：")
    print("   pip install openai python-dotenv")
    raise

# -------------------------------------------------------------------
# 1. 加载 .env 文件（优先加载项目根目录的 .env）
# -------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent
env_path = ROOT_DIR / ".env"

if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ 已加载环境文件: {env_path}")
else:
    print("⚠️ 未在项目根目录找到 .env，将直接使用系统环境变量。")

# -------------------------------------------------------------------
# 2. 读取必须的环境变量
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

endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
api_key = os.environ["AZURE_OPENAI_API_KEY"]
deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]
api_version = os.environ["AZURE_OPENAI_API_VERSION"]

print("\n🔧 当前配置：")
print(f"   AZURE_OPENAI_ENDPOINT   = {endpoint}")
print(f"   AZURE_OPENAI_DEPLOYMENT = {deployment}")
print(f"   AZURE_OPENAI_API_VERSION= {api_version}")

# -------------------------------------------------------------------
# 3. 创建 AzureOpenAI 客户端并发起一次简单请求
# -------------------------------------------------------------------
print("\n🚀 正在尝试连接 Azure OpenAI...")

client = AzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=endpoint,
)

try:
    response = client.chat.completions.create(
        model=deployment,  # 这里用的是部署名
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in one short sentence."},
        ],
        max_tokens=20,
    )

    choice = response.choices[0]
    print("\n✅ 调用成功！返回内容示例：")
    print("-" * 60)
    print(choice.message.content)
    print("-" * 60)

    print("\n📊 一些调试信息：")
    print(f"   id:        {response.id}")
    print(f"   model:     {response.model}")
    print(f"   created:   {response.created}")
    print("   usage:     ", response.usage)

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

# llm_client.py
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
import os, httpx

load_dotenv()

# 支持 PROXY_URL / HTTPS_PROXY / HTTP_PROXY 三选一
proxy = os.getenv("PROXY_URL") or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
proxies = {"http": proxy, "https": proxy} if proxy else None

# 显式把代理注入到 httpx，确保 LangChain/OpenAI 走同一路由
http_client = httpx.Client(
    proxies=proxies,
    timeout=30.0,
    transport=httpx.HTTPTransport(retries=3),
)

def get_llm(deployment_name: str | None = None, temperature: float | None = None):
    return AzureChatOpenAI(
        deployment_name=deployment_name or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
        temperature=1.0 if temperature is None else temperature,
        http_client=http_client,
    )

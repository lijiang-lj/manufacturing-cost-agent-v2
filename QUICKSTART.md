# 快速入门指南

## 5分钟上手 Manufacturing Cost Agent

### 第1步：解压项目

```bash
# 解压下载的压缩包
tar -xzf manufacturing-cost-agent-v2.tar.gz
cd manufacturing-cost-agent-v2
```

### 第2步：安装依赖

**选择一种方式：**

#### 方式 A：使用 Conda（推荐）
```bash
conda env create -f environment.yml
conda activate manufacturing-cost-agent
```

#### 方式 B：使用 pip
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 第3步：配置环境

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件
# 填入您的 Azure OpenAI 配置：
# AZURE_OPENAI_API_KEY=your_key
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

### 第4步：运行测试

```bash
# 运行简单验证
python simple_test.py

# 运行完整测试（可选）
python tests/test_agent.py
```

### 第5步：开始使用

```python
from agent import run_agent

# 估算工艺成本
result = run_agent(
    query="估算 melting, casting, machining, inspection 的价格",
    production_volume=1_100_000,
    location="Ningbo, Zhejiang"
)

# 查看结果
print(f"总成本: {result['total_cost']:.2f} CNY/kg")
```

## 常见用例

### 用例 1：估算单个工艺

```python
result = run_agent("估算 casting 工艺的成本")
```

### 用例 2：带图纸估算

```python
result = run_agent(
    query="基于图纸估算成本",
    drawing_path="data/part.stp"
)
```

### 用例 3：对比不同地区

```python
for loc in ["Ningbo, Zhejiang", "Nanjing, Jiangsu"]:
    result = run_agent(
        query="估算 machining 成本",
        location=loc
    )
```

## 故障排查

### 问题1：Azure OpenAI 连接失败

**解决**：
1. 检查 API Key 是否正确
2. 确认 Endpoint 格式（需要 https://）
3. 验证部署名称

### 问题2：CadQuery 导入错误

**解决**：
```bash
# 使用 conda 安装
conda install -c conda-forge cadquery
```

### 问题3：LLM 返回格式错误

**说明**：系统已内置默认值，会自动降级处理

## 下一步

- 📖 阅读完整文档：`README.md`
- 🎓 查看使用指南：`docs/USAGE_GUIDE.md`
- 🏗️ 了解架构：`docs/ARCHITECTURE.md`
- 🧪 运行完整测试：`python tests/test_agent.py`

## 技术支持

查看文档中的常见问题部分，或检查项目 Issues。

---

**祝您使用愉快！** 🎉

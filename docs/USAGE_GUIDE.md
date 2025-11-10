# Manufacturing Cost Agent 使用指南

## 目录

1. [快速开始](#快速开始)
2. [环境配置](#环境配置)
3. [基本使用](#基本使用)
4. [高级用法](#高级用法)
5. [常见问题](#常见问题)

## 快速开始

### 第一步：安装

```bash
# 克隆项目（或解压下载的压缩包）
cd manufacturing-cost-agent-v2

# 使用 Conda 创建环境（推荐）
conda env create -f environment.yml
conda activate manufacturing-cost-agent

# 或使用 pip
pip install -r requirements.txt
```

### 第二步：配置

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入您的 Azure OpenAI 配置
# AZURE_OPENAI_API_KEY=your_key
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

### 第三步：运行测试

```bash
# 运行测试用例
python tests/test_agent.py

# 或直接使用 agent.py
python agent.py
```

## 环境配置

### Azure OpenAI 配置

1. **获取 API Key**
   - 登录 Azure Portal
   - 找到您的 OpenAI 资源
   - 在"密钥和终结点"中复制密钥

2. **获取 Endpoint**
   - 格式：`https://your-resource-name.openai.azure.com/`
   - 注意必须包含 `https://` 前缀

3. **确认部署名称**
   - 在 Azure OpenAI Studio 中查看您的部署名称
   - 常见名称：`gpt-4o`, `gpt-4o-mini`, `gpt-35-turbo`

### 代理设置（可选）

如果您在企业网络环境中：

```env
PROXY_URL=http://proxy.company.com:8080
```

### 默认参数设置（可选）

```env
DEFAULT_PRODUCTION_VOLUME=1100000
DEFAULT_LOCATION=Ningbo, Zhejiang
```

## 基本使用

### 示例 1：估算单个工艺

```python
from agent import run_agent

# 估算熔炼工艺成本
result = run_agent(
    query="估算 melting 工艺的价格",
    production_volume=1_100_000,
    location="Ningbo, Zhejiang"
)

# 查看结果
print(result['cost_breakdown']['melting'])
```

### 示例 2：估算多个工艺

```python
# 估算完整生产流程
result = run_agent(
    query="估算 melting, casting, machining, inspection 的费率",
    production_volume=1_100_000,
    location="Ningbo, Zhejiang"
)

# 查看总成本
print(f"总成本: {result['total_cost']} CNY/kg")
```

### 示例 3：使用自然语言查询

系统支持灵活的自然语言输入：

```python
# 以下查询都是有效的：
queries = [
    "帮我算一下铸造和机加工多少钱",
    "Calculate the cost for melting and casting",
    "我想知道 inspection 工艺的费率",
    "估算 OP（机加工）的价格"
]

for q in queries:
    result = run_agent(query=q)
```

## 高级用法

### 1. 图纸解析

```python
# 带图纸的成本估算
result = run_agent(
    query="基于图纸估算成本",
    drawing_path="data/part.stp",
    production_volume=1_100_000,
    location="Ningbo, Zhejiang"
)

# 查看解析的几何参数
if result.get('drawing_data'):
    print(f"表面积: {result['drawing_data']['surface_area']} mm²")
    print(f"体积: {result['drawing_data']['volume']} mm³")
```

### 2. 批量估算（不同地区）

```python
from agent import run_agent

locations = [
    "Ningbo, Zhejiang",
    "Nanjing, Jiangsu",
    "Shenzhen, Guangdong",
    "Chengdu, Sichuan"
]

results = {}
for loc in locations:
    result = run_agent(
        query="估算 machining 的成本",
        production_volume=1_100_000,
        location=loc
    )
    results[loc] = result['processes']['machining']['total']

# 对比结果
for loc, cost in results.items():
    print(f"{loc}: {cost:.2f} CNY/kg")
```

### 3. 产量敏感性分析

```python
volumes = [10_000, 100_000, 500_000, 1_100_000, 5_000_000]

results = {}
for vol in volumes:
    result = run_agent(
        query="估算 casting 的成本",
        production_volume=vol,
        location="Ningbo, Zhejiang"
    )
    results[vol] = result['processes']['casting']['total']

# 可视化（需要 matplotlib）
import matplotlib.pyplot as plt

plt.plot(list(results.keys()), list(results.values()), marker='o')
plt.xlabel('产量（件）')
plt.ylabel('成本（CNY/kg）')
plt.title('产量对成本的影响')
plt.xscale('log')
plt.grid(True)
plt.show()
```

### 4. 成本分解分析

```python
result = run_agent(
    query="估算 melting 的成本",
    production_volume=1_100_000,
    location="Ningbo, Zhejiang"
)

melting = result['processes']['melting']

print("成本分解：")
print(f"  设备折旧: {melting['equipment_depreciation']:.2f} CNY/kg")
print(f"  能源消耗: {melting['energy']:.2f} CNY/kg")
print(f"  人工成本: {melting['labor']:.2f} CNY/kg")
print(f"  规模效应: {melting['volume_adjustment']:+.2f} CNY/kg")
print(f"  总计: {melting['total']:.2f} CNY/kg")
```

### 5. 自定义 Agent 行为

如果需要修改 Agent 的推理逻辑：

```python
# 编辑 agent.py 中的节点函数
# 例如，修改 execution_node() 来添加新的成本项

def execution_node(state: AgentState) -> AgentState:
    # ... 原有代码 ...
    
    # 添加新的成本项：质量检测成本
    quality_cost = 0.50  # 假设固定成本
    
    for process in processes:
        # ... 原有计算 ...
        
        # 添加到总成本
        total += quality_cost
        cost_breakdown[process]['quality'] = quality_cost
    
    # ... 原有代码 ...
```

## 常见问题

### Q1: 为什么估算结果每次运行都略有不同？

**A**: 因为系统使用 LLM 进行推理，每次调用可能产生略微不同的结果。这是正常的。如需更稳定的结果，可以：
- 降低 `temperature` 参数（在 `agent.py` 中修改）
- 多次运行取平均值
- 使用缓存机制

### Q2: 可以不使用图纸吗？

**A**: 可以！系统在没有图纸时会基于经验进行合理估算。图纸主要用于提高估算精度。

### Q3: 支持哪些工艺类型？

**A**: 目前支持：
- `melting`（熔炼）
- `casting`（铸造）
- `machining` / `OP`（机加工）
- `inspection`（检验）

您可以在 `agent.py` 中添加更多工艺类型。

### Q4: 如何添加新的工艺类型？

**A**: 
1. 在 `execution_node()` 的 `all_processes` 列表中添加新工艺名
2. LLM 会自动推理新工艺的成本构成

```python
all_processes = ["melting", "casting", "machining", "inspection", "welding"]  # 添加 welding
```

### Q5: CadQuery 安装失败怎么办？

**A**: 
```bash
# 方法1: 使用 conda（最可靠）
conda install -c conda-forge cadquery

# 方法2: 跳过图纸解析功能
# 系统会自动检测并继续运行，只是无法解析图纸
```

### Q6: 如何调整 LLM 的推理精度？

**A**: 在 `agent.py` 中修改模型参数：

```python
llm = AzureChatOpenAI(
    deployment_name="gpt-4o",
    temperature=0.3,  # 降低随机性，默认 0.7
    # ... 其他参数
)
```

### Q7: 估算结果不合理怎么办？

**A**: 检查以下几点：
1. 确认输入的产量和地点合理
2. 检查 LLM 模型是否正确（建议使用 GPT-4o）
3. 查看各工具的默认值是否符合您的情况
4. 考虑在提示词中添加更多上下文信息

### Q8: 如何导出结果？

**A**: 
```python
import json

result = run_agent(query="...")

# 导出为 JSON
with open('cost_report.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

# 或导出为 CSV
import pandas as pd

processes = result['processes']
df = pd.DataFrame(processes).T
df.to_csv('cost_report.csv')
```

### Q9: 支持并行处理多个查询吗？

**A**: 可以，但需要注意 Azure OpenAI 的 API 速率限制。示例：

```python
from concurrent.futures import ThreadPoolExecutor

def estimate_cost(query):
    return run_agent(query=query)

queries = [
    "估算 melting 的成本",
    "估算 casting 的成本",
    "估算 machining 的成本"
]

with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(estimate_cost, queries))
```

### Q10: 如何集成到现有系统？

**A**: 
```python
# 作为 Python 模块导入
from agent import run_agent

# 或封装为 REST API（使用 FastAPI）
from fastapi import FastAPI
app = FastAPI()

@app.post("/estimate")
def estimate(query: str, volume: int, location: str):
    result = run_agent(query, production_volume=volume, location=location)
    return result
```

## 性能优化建议

### 1. 使用缓存

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_estimate(process: str, volume: int, location: str):
    result = run_agent(
        query=f"估算 {process} 的成本",
        production_volume=volume,
        location=location
    )
    return result['processes'][process]['total']
```

### 2. 批量处理

一次查询多个工艺比多次单独查询更高效：

```python
# ✅ 推荐
result = run_agent(query="估算 melting, casting, machining 的成本")

# ❌ 不推荐
for process in ["melting", "casting", "machining"]:
    result = run_agent(query=f"估算 {process} 的成本")
```

### 3. 降低 LLM 调用次数

如果只需要粗略估算，可以使用默认值：

```python
# 直接使用工具的默认值，跳过 LLM 推理
from tools.equipment_depreciation_tool import EquipmentDepreciationTool

tool = EquipmentDepreciationTool(llm)
# 修改 run() 方法直接返回默认值
```

## 下一步

- 查看 [README.md](README.md) 了解系统架构
- 运行 [tests/test_agent.py](tests/test_agent.py) 查看完整示例
- 根据您的需求修改工具和提示词

## 技术支持

如有问题，请检查：
1. [README.md](README.md) 的故障排查部分
2. 项目 Issues（如有）
3. Azure OpenAI 文档

---

**祝您使用愉快！** 🚀

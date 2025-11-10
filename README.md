# Manufacturing Cost Agent

## 项目简介

Manufacturing Cost Agent 是一个基于 LangGraph 和 Azure OpenAI GPT-4o 的智能工艺价格查询系统。系统能够自动推理和估算制造工艺的成本，支持图纸解析、多工艺分析和地域成本差异计算。

## 核心特性

- ✅ **完全 LLM 驱动**：所有价格推理由 GPT-4o 完成，无硬编码价格表
- ✅ **图纸解析支持**：使用 CadQuery 解析 STP/STEP 文件提取几何参数
- ✅ **多维度成本分析**：
  - 设备折旧成本
  - 产量规模效应
  - 能源成本（电/水/气）
  - 人工成本（考虑地域差异）
- ✅ **智能推理**：即使不提供图纸也能合理估算
- ✅ **地域适配**：考虑中国不同地区的工资和能源价格差异

## 系统架构

```
manufacturing-cost-agent-v2/
├── agent.py                 # 主Agent逻辑（LangGraph）
├── tools/                   # 工具模块
│   ├── drawing_parser_tool.py         # STP图纸解析
│   ├── equipment_depreciation_tool.py # 设备折旧估算
│   ├── production_volume_tool.py      # 产量影响分析
│   ├── energy_cost_tool.py            # 能源成本估算
│   └── labor_cost_tool.py             # 人工成本估算
├── tests/                   # 测试用例
│   └── test_agent.py
├── docs/                    # 文档
├── data/                    # 数据文件（图纸等）
├── environment.yml          # Conda环境配置
├── requirements.txt         # Python依赖
└── .env.example            # 环境变量模板
```

## 快速开始

### 1. 环境准备

#### 方式 A：使用 Conda（推荐）

```bash
# 创建环境
conda env create -f environment.yml

# 激活环境
conda activate manufacturing-cost-agent
```

#### 方式 B：使用 pip

```bash
# 创建虚拟环境（Python 3.13）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入您的配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# 可选：代理设置
PROXY_URL=

# 可选：默认参数
DEFAULT_PRODUCTION_VOLUME=1100000
DEFAULT_LOCATION=Ningbo, Zhejiang
```

### 3. 运行测试

```bash
# 基本测试
python tests/test_agent.py

# 或直接运行主程序
python agent.py
```

## 使用示例

### 示例 1：基本工艺估算

```python
from agent import run_agent

# 估算4个工艺的费率
result = run_agent(
    query="估算 melting, casting, machining, inspection 的价格",
    production_volume=1_100_000,
    location="Ningbo, Zhejiang"
)
```

**输出示例**：
```json
{
  "timestamp": "2024-11-10 15:30:00",
  "location": "Ningbo, Zhejiang",
  "production_volume": 1100000,
  "unit": "CNY/kg",
  "processes": {
    "melting": {
      "equipment_depreciation": 0.50,
      "energy": 2.50,
      "labor": 0.40,
      "volume_adjustment": -0.30,
      "total": 3.10
    },
    "casting": {
      "equipment_depreciation": 1.20,
      "energy": 1.20,
      "labor": 0.60,
      "volume_adjustment": -0.30,
      "total": 2.70
    },
    "machining": {
      "equipment_depreciation": 0.80,
      "energy": 1.80,
      "labor": 0.50,
      "volume_adjustment": -0.30,
      "total": 2.80
    },
    "inspection": {
      "equipment_depreciation": 0.30,
      "energy": 0.30,
      "labor": 0.80,
      "volume_adjustment": -0.30,
      "total": 1.10
    }
  },
  "total_cost": 9.70
}
```

### 示例 2：带图纸解析

```python
result = run_agent(
    query="基于图纸估算 melting 和 casting 的成本",
    drawing_path="data/part.stp",
    production_volume=1_100_000,
    location="Ningbo, Zhejiang"
)
```

系统会自动解析图纸的表面积和体积，用于精确估算能源消耗。

### 示例 3：不同地区对比

```python
locations = ["Ningbo, Zhejiang", "Nanjing, Jiangsu", "Chengdu, Sichuan"]

for loc in locations:
    result = run_agent(
        query="估算 machining 的成本",
        production_volume=1_100_000,
        location=loc
    )
```

### 示例 4：产量影响分析

```python
volumes = [50_000, 500_000, 1_100_000, 5_000_000]

for vol in volumes:
    result = run_agent(
        query="估算 casting 的成本",
        production_volume=vol,
        location="Ningbo, Zhejiang"
    )
```

## 工艺类型说明

系统支持以下工艺类型：

| 工艺 | 说明 | 典型成本构成 |
|------|------|-------------|
| **melting** | 熔炼 | 高电耗 + 中等天然气 + 中等人工 |
| **casting** | 铸造 | 高设备折旧 + 中等能耗 + 中等人工 |
| **machining** | 机加工 | 高能耗（CNC）+ 中等设备 + 低人工 |
| **inspection** | 检验 | 低能耗 + 低设备 + 高人工 |

系统还支持别名：
- `OP` → `machining`（机加工操作）

## 成本计算逻辑

每个工艺的总成本 = **设备折旧** + **能源成本** + **人工成本** + **产量调整**

### 1. 设备折旧成本

由 LLM 推理：
- 设备类型和采购成本
- 折旧年限（5-10年）
- 年度折旧分摊

### 2. 能源成本

考虑因素：
- 地区电价（工业用电）
- 水价（冷却用水）
- 天然气价格
- 工艺能耗特性

### 3. 人工成本

考虑因素：
- 地区工资水平
- 工艺自动化程度
- 所需人员数量
- 社保公积金（约40%）

### 4. 产量调整

规模效应：
- 小批量（<10万）：+20%~+50%
- 中批量（10-50万）：-5%~+10%
- 大批量（50-100万）：-10%~-20%
- 超大批量（>100万）：-20%~-30%

## 图纸解析功能

### 支持的文件格式

- STP (STEP) 文件
- STEP 文件

### 提取的参数

- **表面积**（mm²）：用于估算表面处理、涂装能耗
- **体积**（mm³）：用于估算材料用量、熔炼能耗

### 使用说明

1. 将 STP 文件放在 `data/` 目录下
2. 在调用 `run_agent()` 时传入 `drawing_path` 参数
3. 系统会自动解析并应用到成本估算

**注意**：如果未安装 CadQuery，图纸解析功能将不可用，但系统仍能基于经验进行估算。

## 地域价格数据

系统内置了中国主要地区的参考价格（2024年）：

### 工业电价

| 地区 | 电价（CNY/kWh） |
|------|----------------|
| 浙江 | 0.60 - 0.70 |
| 江苏 | 0.55 - 0.65 |
| 广东 | 0.65 - 0.75 |

### 平均工资

| 地区 | 月工资（CNY） |
|------|--------------|
| 长三角 | 5000 - 8000 |
| 珠三角 | 5500 - 8500 |
| 中西部 | 4000 - 6000 |

## API 参考

### run_agent()

主函数，运行成本估算Agent。

**参数**：

- `query` (str): 用户查询，如 "估算 melting 和 casting 的价格"
- `drawing_path` (str, optional): STP图纸文件路径
- `production_volume` (int, optional): 年产量，默认从环境变量读取
- `location` (str, optional): 生产地点，默认从环境变量读取

**返回**：

包含成本分析结果的字典，结构如下：

```python
{
    "timestamp": "2024-11-10 15:30:00",
    "location": "Ningbo, Zhejiang",
    "production_volume": 1100000,
    "unit": "CNY/kg",
    "processes": {
        "process_name": {
            "equipment_depreciation": float,
            "energy": float,
            "labor": float,
            "volume_adjustment": float,
            "total": float
        }
    },
    "total_cost": float,
    "drawing_data": {...}  # 如果提供了图纸
}
```

## 测试用例

运行完整测试套件：

```bash
python tests/test_agent.py
```

测试包括：

1. **基本查询测试**：估算4个工艺（无图纸）
2. **图纸解析测试**：带STP文件的成本估算
3. **地域对比测试**：不同地区的成本差异
4. **产量影响测试**：不同产量的规模效应

## 故障排查

### 问题：CadQuery 安装失败

**解决方案**：
```bash
# 使用 conda 安装（推荐）
conda install -c conda-forge cadquery

# 或使用 pip（可能需要额外依赖）
pip install cadquery
```

### 问题：Azure OpenAI 连接失败

**检查清单**：
1. 确认 API Key 正确
2. 确认 Endpoint 格式正确（需包含 `https://`）
3. 确认部署名称与 Azure 门户一致
4. 如在企业网络，检查代理设置

### 问题：LLM 返回格式错误

**说明**：系统已内置默认值，即使LLM推理失败也能返回合理估算。

## 技术栈

- **Python**: 3.13
- **LangChain**: 0.3.27
- **LangGraph**: 0.6.6
- **Azure OpenAI**: GPT-4o
- **CadQuery**: 2.6.1（图纸解析）
- **Pydantic**: 2.11.7（数据验证）

## 性能优化建议

1. **缓存机制**：对相同工艺的估算结果可以缓存
2. **批量处理**：一次性估算多个工艺可减少LLM调用次数
3. **并行处理**：不同工艺的估算可以并行执行

## 许可证

MIT License

## 联系方式

如有问题或建议，请联系项目维护者。

---

**最后更新**: 2024-11-10

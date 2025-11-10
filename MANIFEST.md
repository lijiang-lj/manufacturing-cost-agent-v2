# Manufacturing Cost Agent - 项目清单

## 文件结构

```
manufacturing-cost-agent-v2/
│
├── 📄 README.md                          # 项目主文档
├── 📄 QUICKSTART.md                      # 5分钟快速入门
├── 📄 VERSION                            # 版本信息
├── 📄 .env.example                       # 环境变量模板
│
├── 📦 依赖配置
│   ├── environment.yml                   # Conda环境配置
│   └── requirements.txt                  # Python依赖列表
│
├── 🤖 核心代码
│   ├── agent.py                          # 主Agent逻辑（LangGraph）
│   └── simple_test.py                    # 简单测试脚本
│
├── 🛠️ tools/                             # 工具模块
│   ├── __init__.py                       # 包初始化
│   ├── drawing_parser_tool.py            # STP图纸解析工具
│   ├── equipment_depreciation_tool.py    # 设备折旧估算工具
│   ├── production_volume_tool.py         # 产量影响分析工具
│   ├── energy_cost_tool.py               # 能源成本估算工具
│   └── labor_cost_tool.py                # 人工成本估算工具
│
├── 📚 docs/                               # 文档目录
│   ├── USAGE_GUIDE.md                    # 详细使用指南
│   └── ARCHITECTURE.md                   # 架构设计文档
│
├── 🧪 tests/                              # 测试目录
│   └── test_agent.py                     # 完整测试套件
│
├── 📁 data/                               # 数据目录（用户自行添加）
│   └── (放置STP图纸文件)
│
└── 📁 config/                             # 配置目录（预留）
    └── (可添加自定义配置)
```

## 文件说明

### 📄 文档文件

| 文件 | 说明 | 用途 |
|------|------|------|
| README.md | 项目主文档 | 了解项目概况、特性和API |
| QUICKSTART.md | 快速入门 | 5分钟上手使用 |
| USAGE_GUIDE.md | 使用指南 | 详细使用方法和示例 |
| ARCHITECTURE.md | 架构文档 | 了解系统设计和扩展 |
| VERSION | 版本信息 | 版本号和更新日志 |

### 🛠️ 核心代码

| 文件 | 行数 | 说明 |
|------|------|------|
| agent.py | ~200 | 主Agent逻辑，LangGraph工作流 |
| simple_test.py | ~130 | 简单验证脚本 |

### 🔧 工具模块

| 文件 | 说明 | 输入 | 输出 |
|------|------|------|------|
| drawing_parser_tool.py | 图纸解析 | STP文件路径 | 表面积/体积 |
| equipment_depreciation_tool.py | 设备折旧 | 工艺+产量 | CNY/kg |
| production_volume_tool.py | 产量影响 | 工艺+产量 | 调整值 |
| energy_cost_tool.py | 能源成本 | 工艺+地点+几何 | CNY/kg |
| labor_cost_tool.py | 人工成本 | 工艺+地点+产量 | CNY/kg |

### 🧪 测试文件

| 文件 | 说明 | 运行方式 |
|------|------|----------|
| simple_test.py | 基本验证 | `python simple_test.py` |
| tests/test_agent.py | 完整测试 | `python tests/test_agent.py` |

### ⚙️ 配置文件

| 文件 | 说明 | 格式 |
|------|------|------|
| .env.example | 环境变量模板 | KEY=value |
| environment.yml | Conda环境 | YAML |
| requirements.txt | Python依赖 | package==version |

## 代码统计

| 类别 | 文件数 | 代码行数（估算） |
|------|--------|-----------------|
| 核心代码 | 1 | ~200 |
| 工具模块 | 5 | ~600 |
| 测试代码 | 2 | ~200 |
| 文档 | 5 | ~2000 |
| **总计** | **13** | **~3000** |

## 依赖清单

### Python 核心依赖

```
langchain==0.3.27
langchain-openai==0.3.35
langchain-community==0.3.31
langchain-core==0.3.79
langgraph==0.6.6
```

### 辅助依赖

```
azure-identity==1.19.0
python-dotenv==1.1.1
cadquery==2.6.1
pydantic==2.11.7
httpx==0.28.1
requests==2.32.5
```

### 环境要求

- **Python**: 3.13+
- **Conda**: 可选，推荐使用
- **Azure OpenAI**: GPT-4o 部署

## 使用检查清单

### ✅ 安装前

- [ ] Python 3.13 已安装
- [ ] 有 Azure OpenAI 访问权限
- [ ] API Key 已获取

### ✅ 安装时

- [ ] 虚拟环境已创建
- [ ] 依赖已安装
- [ ] .env 已配置

### ✅ 首次运行

- [ ] 运行 `simple_test.py` 通过
- [ ] 环境变量正确
- [ ] LLM 连接成功

### ✅ 生产使用

- [ ] 测试用例通过
- [ ] 理解成本计算逻辑
- [ ] 根据需求调整参数

## 快速命令参考

```bash
# 安装
conda env create -f environment.yml
conda activate manufacturing-cost-agent

# 配置
cp .env.example .env
# 编辑 .env

# 测试
python simple_test.py
python tests/test_agent.py

# 使用
python agent.py
```

## 更新日志

### v2.0.0 (2024-11-10)
- 初始发布
- 完整的LangGraph实现
- 5个成本估算工具
- 完整文档和测试

## 已知限制

1. CadQuery 安装可能需要额外配置
2. 图纸解析仅支持 STP/STEP 格式
3. 成本估算依赖 LLM 推理（可能有波动）
4. 地域数据为 2024 年参考值

## 未来计划

- [ ] 支持更多图纸格式（IGS, DWG）
- [ ] 添加材料成本估算
- [ ] 集成实时价格API
- [ ] Web界面开发
- [ ] 数据库持久化

## 贡献指南

欢迎贡献！可以通过以下方式：
1. 报告Bug
2. 提出新功能建议
3. 提交代码改进
4. 完善文档

## 许可证

MIT License - 详见 LICENSE 文件（如有）

---

**文档版本**: 1.0  
**最后更新**: 2024-11-10

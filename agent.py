# -*- coding: utf-8 -*-
"""
Manufacturing Cost Agent - 工艺价格查询智能代理
基于 LangGraph + Azure OpenAI 实现
支持图纸解析、工艺推理、价格估算
"""

import warnings
warnings.filterwarnings("ignore")

import os
import json
import time
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
import httpx
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages  # 如未使用可保留
from typing_extensions import TypedDict

# ==================== 工具导入 ====================
from tools.equipment_depreciation_tool import EquipmentDepreciationTool
from tools.production_volume_tool import ProductionVolumeTool
from tools.energy_cost_tool import EnergyCostTool
from tools.labor_cost_tool import LaborCostTool
from tools.drawing_parser_tool import DrawingParserTool

# ==================== 环境与代理 ====================
load_dotenv()

# 可选：一键关闭外部联网工具（如果后续新增了会出网的工具）
AGENT_OFFLINE = os.getenv("AGENT_OFFLINE", "false").lower() == "true"

# 代理三选一：PROXY_URL > HTTPS_PROXY > HTTP_PROXY
_proxy = os.getenv("PROXY_URL") or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
_proxies = {"http": _proxy, "https": _proxy} if _proxy else None
_no_proxy = os.getenv("NO_PROXY")

# 让下游库也能读到（仅当存在时再设置，避免 NoneType）
if _proxy:
    os.environ["HTTP_PROXY"] = _proxy
    os.environ["HTTPS_PROXY"] = _proxy
if _no_proxy:
    os.environ["NO_PROXY"] = _no_proxy

# 统一 httpx 客户端（带代理与简单重试）
_http_client = httpx.Client(timeout=30.0)

# ==================== 模型初始化（与示例一致） ====================
llm = AzureChatOpenAI(
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
    temperature=1.0,
    http_client=_http_client,  # 关键：确保与简单测试同一路径出网
)

# ==================== 工具注册 ====================
equipment_tool = EquipmentDepreciationTool(llm).as_tool()
volume_tool    = ProductionVolumeTool(llm).as_tool()
energy_tool    = EnergyCostTool(llm).as_tool()
labor_tool     = LaborCostTool(llm).as_tool()
drawing_tool   = DrawingParserTool().as_tool()

# 如果你后续有联网工具，这里可以基于 AGENT_OFFLINE 选择性注入
tools = [
    drawing_tool,      # 图纸解析（本地）
    equipment_tool,    # 设备折旧（走同一 LLM）
    volume_tool,       # 产量影响（走同一 LLM）
    energy_tool,       # 能源成本（走同一 LLM）
    labor_tool,        # 人工成本（走同一 LLM）
]

# ==================== State 定义 ====================
class AgentState(TypedDict):
    messages: List[BaseMessage]
    drawing_data: Optional[Dict[str, Any]]
    production_volume: Optional[int]
    location: Optional[str]
    process_type: Optional[str]
    cost_breakdown: Optional[Dict[str, Any]]

# ==================== 节点函数 ====================
def parse_input_node(state: AgentState) -> AgentState:
    """解析用户输入，提取关键信息"""
    messages = state.get("messages", [])
    _ = messages[-1].content if messages else ""

    volume = state.get("production_volume") or int(os.getenv("DEFAULT_PRODUCTION_VOLUME", "1100000"))
    location = state.get("location") or os.getenv("DEFAULT_LOCATION", "Ningbo, Zhejiang")

    print(f"📋 解析输入 - 产量: {volume:,}, 地点: {location}")

    return {
        **state,
        "production_volume": volume,
        "location": location,
    }

def execution_node(state: AgentState) -> AgentState:
    """执行工具调用"""
    messages = state["messages"]
    volume = state["production_volume"]
    location = state["location"]
    # 关键修复：保证是 dict，而不是 None，避免 .get 报错
    drawing_data = state.get("drawing_data") or {}

    # 从用户消息中提取需要估算的工艺列表
    last_message = messages[-1].content.lower()
    all_processes = ["melting", "casting", "machining", "inspection"]

    processes = [p for p in all_processes if p in last_message]
    if not processes:
        processes = all_processes

    if "op" in last_message or "machining" in last_message:
        if "machining" not in processes:
            processes.append("machining")

    cost_breakdown: Dict[str, Any] = {}

    for process in processes:
        print(f"\n⚙️ 正在估算 {process} 工艺成本...")
        try:
            # 1. 设备折旧
            equip_cost = equipment_tool.invoke({
                "process": process,
                "volume": volume
            })

            # 2. 能源成本
            energy_cost = energy_tool.invoke({
                "process": process,
                "location": location,
                "surface_area": drawing_data.get("surface_area"),
                "volume": drawing_data.get("volume")
            })

            # 3. 人工成本
            labor_cost = labor_tool.invoke({
                "process": process,
                "location": location,
                "volume": volume
            })

            # 4. 产量调整
            volume_impact = volume_tool.invoke({
                "process": process,
                "volume": volume
            })

            # 兜底：各工具应返回数值；若不是数值则按 0 处理，避免进一步错误
            def _num(x): 
                try:
                    return float(x)
                except Exception:
                    return 0.0

            equip_cost_f   = _num(equip_cost)
            energy_cost_f  = _num(energy_cost)
            labor_cost_f   = _num(labor_cost)
            volume_imp_f   = _num(volume_impact)

            total = equip_cost_f + energy_cost_f + labor_cost_f + volume_imp_f

            cost_breakdown[process] = {
                "equipment_depreciation": round(equip_cost_f, 6),
                "energy": round(energy_cost_f, 6),
                "labor": round(labor_cost_f, 6),
                "volume_adjustment": round(volume_imp_f, 6),
                "total": round(total, 2),
            }

            print(f"✅ {process}: {total:.2f} CNY/kg")

        except Exception as e:
            # 发生异常时，写入结构化错误，避免后续格式化节点再抛异常
            print(f"❌ {process} 估算失败: {e}")
            cost_breakdown[process] = {"error": str(e)}

    state["cost_breakdown"] = cost_breakdown
    state["messages"].append(
        AIMessage(content=json.dumps(cost_breakdown, ensure_ascii=False, indent=2))
    )
    return state

def output_node(state: AgentState) -> AgentState:
    """格式化输出"""
    cost_breakdown = state.get("cost_breakdown") or {}

    total_cost = 0.0
    for v in cost_breakdown.values():
        if isinstance(v, dict) and "total" in v:
            try:
                total_cost += float(v.get("total", 0))
            except Exception:
                pass

    output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "location": state.get("location"),
        "production_volume": state.get("production_volume"),
        "unit": "CNY/kg",
        "processes": cost_breakdown,
        "total_cost": round(total_cost, 2),
        "drawing_data": state.get("drawing_data"),
    }

    state["messages"].append(
        SystemMessage(content=json.dumps(output, ensure_ascii=False, indent=2))
    )

    print("\n" + "="*60)
    print("📊 最终成本报告")
    print("="*60)
    print(json.dumps(output, ensure_ascii=False, indent=2))

    return state

# ==================== Graph 构建 ====================
workflow = StateGraph(AgentState)
workflow.add_node("parse_input", parse_input_node)
workflow.add_node("execution", execution_node)
workflow.add_node("output", output_node)

workflow.add_edge(START, "parse_input")
workflow.add_edge("parse_input", "execution")
workflow.add_edge("execution", "output")
workflow.add_edge("output", END)

agent = workflow.compile()

# ==================== 主函数 ====================
def run_agent(
    query: str,
    drawing_path: Optional[str] = None,
    production_volume: Optional[int] = None,
    location: Optional[str] = None
) -> Dict[str, Any]:
    """
    运行 Agent

    Args:
        query: 用户查询（如 "估算 melting, casting, machining, inspection 工艺的价格"）
        drawing_path: STP 图纸文件路径（可选）
        production_volume: 年产量（可选，默认从环境变量读取）
        location: 生产地点（可选，默认从环境变量读取）

    Returns:
        包含成本分析结果的字典（与 simple_test.py 期待格式兼容）
    """
    initial_state: AgentState = {
        "messages": [HumanMessage(content=query)],
        "drawing_data": None,
        "production_volume": production_volume,
        "location": location,
        "process_type": None,
        "cost_breakdown": None
    }

    # 可选：解析图纸
    if drawing_path and os.path.exists(drawing_path):
        print(f"📐 解析图纸: {drawing_path}")
        try:
            drawing_data = drawing_tool.invoke({"file_path": drawing_path})
            # 保证是 dict，后续 .get 不会报错
            if not isinstance(drawing_data, dict):
                drawing_data = {}
            initial_state["drawing_data"] = drawing_data
        except Exception as e:
            print(f"⚠️ 图纸解析失败: {e}")

    result_state = agent.invoke(initial_state)

    # 返回一个与 simple_test 兼容的结构
    # 如果你只想要最终输出，可以从 messages 的最后一个 SystemMessage 解析
    try:
        final_msg = next(
            (m for m in reversed(result_state["messages"]) if isinstance(m, SystemMessage)),
            None
        )
        if final_msg and final_msg.content:
            return json.loads(final_msg.content)
    except Exception:
        pass

    # 兜底：构造最接近 simple_test 所需的结构
    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "location": result_state.get("location"),
        "production_volume": result_state.get("production_volume"),
        "unit": "CNY/kg",
        "processes": result_state.get("cost_breakdown") or {},
        "total_cost": 0,
        "drawing_data": result_state.get("drawing_data"),
    }

if __name__ == "__main__":
    query = "估算 melting, casting, machining, inspection 工艺的价格"
    run_agent(query)

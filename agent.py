# -*- coding: utf-8 -*-
"""
Manufacturing Cost Agent - 工艺价格查询智能代理
基于LangGraph + Azure OpenAI GPT-4o实现
支持图纸解析、工艺推理、价格估算
"""

import warnings
warnings.filterwarnings("ignore")

import os
import json
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import (
    BaseMessage, HumanMessage, AIMessage, 
    SystemMessage
)

from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# 导入工具
from tools.equipment_depreciation_tool import EquipmentDepreciationTool
from tools.production_volume_tool import ProductionVolumeTool
from tools.energy_cost_tool import EnergyCostTool
from tools.labor_cost_tool import LaborCostTool
from tools.drawing_parser_tool import DrawingParserTool

# 加载环境变量
load_dotenv()

# ==================== 模型初始化 ====================
llm = AzureChatOpenAI(
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-08-01-preview",
    temperature=0.7
)

# ==================== 工具注册 ====================
equipment_tool = EquipmentDepreciationTool(llm).as_tool()
volume_tool = ProductionVolumeTool(llm).as_tool()
energy_tool = EnergyCostTool(llm).as_tool()
labor_tool = LaborCostTool(llm).as_tool()
drawing_tool = DrawingParserTool().as_tool()

tools = [
    drawing_tool,      # 图纸解析
    equipment_tool,    # 设备折旧
    volume_tool,       # 产量影响
    energy_tool,       # 能源成本
    labor_tool         # 人工成本
]

# ==================== State 定义 ====================
class AgentState(TypedDict):
    messages: List[BaseMessage]
    drawing_data: Optional[Dict[str, Any]]
    production_volume: Optional[int]
    location: Optional[str]
    process_type: Optional[str]
    cost_breakdown: Optional[Dict[str, float]]

# ==================== 节点函数 ====================

def parse_input_node(state: AgentState) -> AgentState:
    """解析用户输入，提取关键信息"""
    messages = state.get("messages", [])
    last_message = messages[-1].content if messages else ""
    
    # 简单提取逻辑（实际项目中可用LLM提取）
    volume = state.get("production_volume") or int(os.getenv("DEFAULT_PRODUCTION_VOLUME", 1100000))
    location = state.get("location") or os.getenv("DEFAULT_LOCATION", "Ningbo, Zhejiang")
    
    print(f"📋 解析输入 - 产量: {volume:,}, 地点: {location}")
    
    return {
        **state,
        "production_volume": volume,
        "location": location
    }

def execution_node(state: AgentState) -> AgentState:
    """执行工具调用"""
    messages = state["messages"]
    volume = state["production_volume"]
    location = state["location"]
    drawing_data = state.get("drawing_data", {})
    
    # 从用户消息中提取需要估算的工艺列表
    last_message = messages[-1].content.lower()
    all_processes = ["melting", "casting", "machining", "inspection"]
    
    # 检测用户提到的工艺
    processes = [p for p in all_processes if p in last_message]
    if not processes:
        processes = all_processes  # 默认估算所有工艺
    
    # 特殊处理：OP = machining
    if "op" in last_message or "machining" in last_message:
        if "machining" not in processes:
            processes.append("machining")
    
    cost_breakdown = {}
    
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
            
            total = equip_cost + energy_cost + labor_cost + volume_impact
            cost_breakdown[process] = {
                "equipment_depreciation": equip_cost,
                "energy": energy_cost,
                "labor": labor_cost,
                "volume_adjustment": volume_impact,
                "total": round(total, 2)
            }
            
            print(f"✅ {process}: {total:.2f} CNY/kg")
            
        except Exception as e:
            print(f"❌ {process} 估算失败: {e}")
            cost_breakdown[process] = {"error": str(e)}
    
    state["cost_breakdown"] = cost_breakdown
    state["messages"].append(
        AIMessage(content=json.dumps(cost_breakdown, ensure_ascii=False, indent=2))
    )
    
    return state

def output_node(state: AgentState) -> AgentState:
    """格式化输出"""
    cost_breakdown = state.get("cost_breakdown", {})
    
    output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "location": state["location"],
        "production_volume": state["production_volume"],
        "unit": "CNY/kg",
        "processes": cost_breakdown,
        "total_cost": sum(
            p.get("total", 0) for p in cost_breakdown.values() if isinstance(p, dict) and "total" in p
        ),
        "drawing_data": state.get("drawing_data")
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
    运行Agent
    
    Args:
        query: 用户查询（如 "估算 melting, casting, machining, inspection 工艺的价格"）
        drawing_path: STP图纸文件路径（可选）
        production_volume: 年产量（可选，默认从环境变量读取）
        location: 生产地点（可选，默认从环境变量读取）
    
    Returns:
        包含成本分析结果的字典
    """
    
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "drawing_data": None,
        "production_volume": production_volume,
        "location": location,
        "process_type": None,
        "cost_breakdown": None
    }
    
    # 如果提供图纸，先解析
    if drawing_path and os.path.exists(drawing_path):
        print(f"📐 解析图纸: {drawing_path}")
        try:
            drawing_data = drawing_tool.invoke({"file_path": drawing_path})
            initial_state["drawing_data"] = drawing_data
        except Exception as e:
            print(f"⚠️ 图纸解析失败: {e}")
    
    result = agent.invoke(initial_state)
    return result

if __name__ == "__main__":
    query = "估算 melting, casting, machining, inspection 工艺的价格"
    run_agent(query)

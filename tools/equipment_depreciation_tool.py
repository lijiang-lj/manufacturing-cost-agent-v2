# -*- coding: utf-8 -*-
"""
equipment_depreciation_tool.py
基于LLM推理的设备折旧成本估算工具
"""

import json
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate


class EquipmentDepreciationArgs(BaseModel):
    process: str = Field(..., description="工艺名称，如 melting, casting, machining, inspection")
    volume: int = Field(..., description="年产量（件数）")


class EquipmentDepreciationTool:
    """设备折旧成本估算工具（完全由LLM推理）"""
    
    def __init__(self, llm: BaseChatModel):
        self.name = "equipment_depreciation"
        self.description = (
            "Estimate equipment depreciation cost (CNY/kg) for a given manufacturing process "
            "and production volume. The LLM will reason about equipment types, costs, "
            "and depreciation rates."
        )
        self.llm = llm
    
    def run(self, process: str, volume: int) -> float:
        """
        估算设备折旧成本
        
        Args:
            process: 工艺类型（melting/casting/machining/inspection）
            volume: 年产量
            
        Returns:
            折旧成本（CNY/kg）
        """
        prompt = ChatPromptTemplate.from_template("""
你是一名制造成本工程师。请估算以下工艺的设备折旧成本（单位：CNY/kg）。

工艺类型: {process}
年产量: {volume:,} 件

请按以下步骤推理：
1. 确定该工艺所需的主要设备类型和数量
2. 估算设备采购成本（考虑自动化程度）
3. 确定设备折旧年限（一般5-10年）
4. 计算年度折旧成本
5. 根据产量分摊到单位产品（假设平均单件重量2kg）

仅返回最终的折旧成本数值（CNY/kg），保留2位小数。
不要解释，只返回数字。

示例输出格式：
0.85
""")
        
        try:
            response = self.llm.invoke(prompt.format(process=process, volume=volume))
            content = response.content.strip()
            
            # 提取数字
            cost = float(content.split('\n')[0].strip())
            print(f"📊 {process} 设备折旧: {cost:.2f} CNY/kg")
            return round(cost, 2)
            
        except Exception as e:
            print(f"⚠️ LLM推理失败，使用默认值: {e}")
            # 默认值（基于经验）
            defaults = {
                "melting": 0.50,
                "casting": 1.20,
                "machining": 0.80,
                "inspection": 0.30
            }
            return defaults.get(process.lower(), 0.50)
    
    def as_tool(self) -> StructuredTool:
        return StructuredTool.from_function(
            func=self.run,
            name=self.name,
            description=self.description,
            args_schema=EquipmentDepreciationArgs
        )

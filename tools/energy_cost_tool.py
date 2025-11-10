# -*- coding: utf-8 -*-
"""
energy_cost_tool.py
基于LLM推理的能源成本估算工具（考虑地域差异）
"""

from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate


class EnergyCostArgs(BaseModel):
    process: str = Field(..., description="工艺名称")
    location: str = Field(..., description="生产地点，如 'Ningbo, Zhejiang'")
    surface_area: Optional[float] = Field(None, description="零件表面积（mm²），用于某些工艺")
    volume: Optional[float] = Field(None, description="零件体积（mm³），用于某些工艺")


class EnergyCostTool:
    """能源成本估算工具（考虑电、水、气和地域差异）"""
    
    def __init__(self, llm: BaseChatModel):
        self.name = "energy_cost"
        self.description = (
            "Estimate energy costs (electricity, water, natural gas) in CNY/kg "
            "for a manufacturing process. Considers regional energy prices. "
            "Surface area and volume are optional parameters."
        )
        self.llm = llm
    
    def run(
        self, 
        process: str, 
        location: str, 
        surface_area: Optional[float] = None,
        volume: Optional[float] = None
    ) -> float:
        """
        估算能源成本
        
        Args:
            process: 工艺类型
            location: 生产地点
            surface_area: 表面积（可选）
            volume: 体积（可选）
            
        Returns:
            能源成本（CNY/kg）
        """
        geo_info = f"\n表面积: {surface_area:.2f} mm²\n体积: {volume:.2f} mm³" if surface_area and volume else ""
        
        prompt = ChatPromptTemplate.from_template("""
你是一名能源成本分析师。请估算以下工艺的能源成本（单位：CNY/kg）。

工艺类型: {process}
生产地点: {location}{geo_info}

请考虑：
1. 该地区的电价（工业用电，考虑峰谷电价）
2. 水价（工业用水）
3. 天然气价格（如需要）
4. 该工艺的典型能耗水平
   - melting: 高电耗（熔炼炉）+ 中等天然气
   - casting: 中等电耗 + 低水耗（冷却）
   - machining: 中等电耗（CNC设备）+ 高水耗（切削液冷却）
   - inspection: 低电耗（检测设备）

中国主要地区工业电价参考（2024）：
- 浙江：0.60-0.70 CNY/kWh
- 江苏：0.55-0.65 CNY/kWh
- 广东：0.65-0.75 CNY/kWh

仅返回总能源成本数值（CNY/kg），保留2位小数。

示例输出：
1.25
""")
        
        try:
            response = self.llm.invoke(
                prompt.format(
                    process=process, 
                    location=location, 
                    geo_info=geo_info
                )
            )
            content = response.content.strip()
            cost = float(content.split('\n')[0].strip())
            print(f"⚡ {process} @ {location} 能源成本: {cost:.2f} CNY/kg")
            return round(cost, 2)
            
        except Exception as e:
            print(f"⚠️ LLM推理失败: {e}")
            # 默认值
            defaults = {
                "melting": 2.50,
                "casting": 1.20,
                "machining": 1.80,
                "inspection": 0.30
            }
            return defaults.get(process.lower(), 1.00)
    
    def as_tool(self) -> StructuredTool:
        return StructuredTool.from_function(
            func=self.run,
            name=self.name,
            description=self.description,
            args_schema=EnergyCostArgs
        )

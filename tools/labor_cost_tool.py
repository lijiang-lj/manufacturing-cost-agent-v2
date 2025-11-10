# -*- coding: utf-8 -*-
"""
labor_cost_tool.py
基于LLM推理的人工成本估算工具（考虑地域差异）
"""

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate


class LaborCostArgs(BaseModel):
    process: str = Field(..., description="工艺名称")
    location: str = Field(..., description="生产地点")
    volume: int = Field(..., description="年产量（件数）")


class LaborCostTool:
    """人工成本估算工具（考虑地域工资差异和自动化程度）"""
    
    def __init__(self, llm: BaseChatModel):
        self.name = "labor_cost"
        self.description = (
            "Estimate labor costs (CNY/kg) considering regional wage levels, "
            "automation degree, and production volume. "
            "Different regions in China have different labor costs."
        )
        self.llm = llm
    
    def run(self, process: str, location: str, volume: int) -> float:
        """
        估算人工成本
        
        Args:
            process: 工艺类型
            location: 生产地点
            volume: 年产量
            
        Returns:
            人工成本（CNY/kg）
        """
        prompt = ChatPromptTemplate.from_template("""
你是一名人力资源成本分析师。请估算以下工艺的人工成本（单位：CNY/kg）。

工艺类型: {process}
生产地点: {location}
年产量: {volume:,} 件

请考虑：
1. 该地区的平均工资水平（2024年数据）
   - 长三角（浙江、江苏、上海）：5000-8000 CNY/月
   - 珠三角（广东）：5500-8500 CNY/月
   - 中西部：4000-6000 CNY/月

2. 该工艺的自动化程度
   - melting: 中等自动化，需要2-3名操作工
   - casting: 高自动化，需要2-4名操作工
   - machining: 高自动化（CNC），需要1-2名操作工/班次
   - inspection: 半自动化，需要3-5名检验员

3. 产量对人工成本的影响
   - 高产量可分摊固定人工成本

4. 社保公积金等附加成本（约工资的40%）

仅返回单位人工成本数值（CNY/kg），保留2位小数。

示例输出：
0.65
""")
        
        try:
            response = self.llm.invoke(
                prompt.format(process=process, location=location, volume=volume)
            )
            content = response.content.strip()
            cost = float(content.split('\n')[0].strip())
            print(f"👷 {process} @ {location} 人工成本: {cost:.2f} CNY/kg")
            return round(cost, 2)
            
        except Exception as e:
            print(f"⚠️ LLM推理失败: {e}")
            # 默认值（基于经验）
            defaults = {
                "melting": 0.40,
                "casting": 0.60,
                "machining": 0.50,
                "inspection": 0.80
            }
            return defaults.get(process.lower(), 0.50)
    
    def as_tool(self) -> StructuredTool:
        return StructuredTool.from_function(
            func=self.run,
            name=self.name,
            description=self.description,
            args_schema=LaborCostArgs
        )

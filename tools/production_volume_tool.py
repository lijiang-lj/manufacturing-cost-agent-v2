# -*- coding: utf-8 -*-
"""
production_volume_tool.py
基于LLM推理的产量规模效应成本调整工具
"""

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate


class ProductionVolumeArgs(BaseModel):
    process: str = Field(..., description="工艺名称")
    volume: int = Field(..., description="年产量（件数）")


class ProductionVolumeTool:
    """产量规模效应成本调整工具"""
    
    def __init__(self, llm: BaseChatModel):
        self.name = "production_volume_impact"
        self.description = (
            "Calculate cost adjustment (CNY/kg) based on production volume. "
            "Economies of scale: higher volume typically reduces unit costs. "
            "Returns positive value for cost reduction, negative for cost increase."
        )
        self.llm = llm
    
    def run(self, process: str, volume: int) -> float:
        """
        计算产量对成本的影响
        
        Args:
            process: 工艺类型
            volume: 年产量
            
        Returns:
            成本调整（CNY/kg），正值表示降低成本，负值表示增加成本
        """
        prompt = ChatPromptTemplate.from_template("""
你是一名制造成本分析师。请估算产量规模对成本的影响。

工艺类型: {process}
年产量: {volume:,} 件

规模效应规律：
- 小批量（<10万）: 成本较高（+20%~50%）
- 中批量（10-50万）: 成本中等（-5%~+10%）
- 大批量（50-100万）: 成本较低（-10%~-20%）
- 超大批量（>100万）: 成本最低（-20%~-30%）

请估算该产量下的成本调整幅度（相对于基准成本1.0 CNY/kg）。

仅返回调整后的成本差值（CNY/kg），保留2位小数。
正值表示成本增加，负值表示成本降低。

示例输出：
-0.15
""")
        
        try:
            response = self.llm.invoke(prompt.format(process=process, volume=volume))
            content = response.content.strip()
            adjustment = float(content.split('\n')[0].strip())
            print(f"📈 {process} 产量影响: {adjustment:+.2f} CNY/kg")
            return round(adjustment, 2)
            
        except Exception as e:
            print(f"⚠️ LLM推理失败: {e}")
            # 简单规则
            if volume > 1000000:
                return -0.30
            elif volume > 500000:
                return -0.15
            elif volume > 100000:
                return 0.0
            else:
                return 0.20
    
    def as_tool(self) -> StructuredTool:
        return StructuredTool.from_function(
            func=self.run,
            name=self.name,
            description=self.description,
            args_schema=ProductionVolumeArgs
        )

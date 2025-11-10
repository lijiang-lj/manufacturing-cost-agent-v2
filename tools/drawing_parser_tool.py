# -*- coding: utf-8 -*-
"""
drawing_parser_tool.py
使用 CadQuery 解析 STP 文件，提取表面积和体积
"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

try:
    import cadquery as cq
    CADQUERY_AVAILABLE = True
except ImportError:
    CADQUERY_AVAILABLE = False
    print("⚠️ CadQuery 未安装，图纸解析功能将不可用")


class DrawingParserArgs(BaseModel):
    file_path: str = Field(..., description="STP文件的完整路径")


class DrawingParserTool:
    """解析STP图纸文件，提取几何参数"""
    
    def __init__(self):
        self.name = "drawing_parser"
        self.description = (
            "Parse STP/STEP CAD files to extract geometric properties "
            "(surface area in mm², volume in mm³). "
            "Returns None if file cannot be parsed."
        )
    
    def run(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        解析STP文件
        
        Args:
            file_path: STP文件路径
            
        Returns:
            包含 surface_area 和 volume 的字典，失败返回None
        """
        if not CADQUERY_AVAILABLE:
            print("❌ CadQuery 未安装")
            return None
        
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return None
        
        try:
            print(f"📐 正在解析图纸: {file_path}")
            
            # 导入STP文件
            result = cq.importers.importStep(file_path)
            
            # 计算表面积（单位：mm²）
            surface_area = 0.0
            for face in result.faces().vals():
                surface_area += face.Area()
            
            # 计算体积（单位：mm³）
            volume = result.val().Volume() if hasattr(result.val(), 'Volume') else 0.0
            
            data = {
                "surface_area": round(surface_area, 2),
                "volume": round(volume, 2),
                "unit_area": "mm²",
                "unit_volume": "mm³"
            }
            
            print(f"✅ 解析成功: 表面积={data['surface_area']} mm², 体积={data['volume']} mm³")
            return data
            
        except Exception as e:
            print(f"❌ 解析失败: {e}")
            return None
    
    def as_tool(self) -> StructuredTool:
        return StructuredTool.from_function(
            func=self.run,
            name=self.name,
            description=self.description,
            args_schema=DrawingParserArgs
        )


if __name__ == "__main__":
    # 测试代码
    tool = DrawingParserTool()
    test_file = "path/to/test.stp"
    result = tool.run(test_file)
    print(result)

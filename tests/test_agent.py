# -*- coding: utf-8 -*-
"""
测试 Manufacturing Cost Agent
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agent import run_agent


def test_basic_query():
    """测试1：基本查询（无图纸）"""
    print("\n" + "="*80)
    print("测试1：基本工艺价格估算（产量=1,100,000）")
    print("="*80)
    
    query = "估算 melting, casting, machining, inspection 这4个工艺的费率"
    result = run_agent(
        query=query,
        production_volume=1_100_000,
        location="Ningbo, Zhejiang"
    )
    
    print("\n✅ 测试1完成")
    return result


def test_with_drawing():
    """测试2：带图纸解析"""
    print("\n" + "="*80)
    print("测试2：带STP图纸的成本估算")
    print("="*80)
    
    # 假设图纸文件路径
    drawing_path = "data/sample.stp"
    
    if not os.path.exists(drawing_path):
        print(f"⚠️ 图纸文件不存在: {drawing_path}")
        print("跳过图纸解析测试")
        return None
    
    query = "基于图纸估算 melting 和 casting 的成本"
    result = run_agent(
        query=query,
        drawing_path=drawing_path,
        production_volume=1_100_000,
        location="Ningbo, Zhejiang"
    )
    
    print("\n✅ 测试2完成")
    return result


def test_different_locations():
    """测试3：不同地区对比"""
    print("\n" + "="*80)
    print("测试3：不同地区成本对比")
    print("="*80)
    
    locations = [
        "Ningbo, Zhejiang",
        "Nanjing, Jiangsu",
        "Chengdu, Sichuan"
    ]
    
    query = "估算 machining 工艺的成本"
    
    for loc in locations:
        print(f"\n📍 地点: {loc}")
        result = run_agent(
            query=query,
            production_volume=1_100_000,
            location=loc
        )
    
    print("\n✅ 测试3完成")


def test_volume_impact():
    """测试4：产量影响对比"""
    print("\n" + "="*80)
    print("测试4：不同产量成本对比")
    print("="*80)
    
    volumes = [50_000, 500_000, 1_100_000, 5_000_000]
    
    query = "估算 casting 工艺的成本"
    
    for vol in volumes:
        print(f"\n📊 产量: {vol:,}")
        result = run_agent(
            query=query,
            production_volume=vol,
            location="Ningbo, Zhejiang"
        )
    
    print("\n✅ 测试4完成")


if __name__ == "__main__":
    # 运行所有测试
    test_basic_query()
    # test_with_drawing()  # 需要真实图纸文件
    test_different_locations()
    test_volume_impact()
    
    print("\n" + "="*80)
    print("所有测试完成！")
    print("="*80)

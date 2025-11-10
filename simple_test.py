# -*- coding: utf-8 -*-
"""
简单测试脚本 - 用于验证系统基本功能
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_basic():
    """基本测试：验证环境配置和导入"""
    print("="*80)
    print("测试1: 验证环境配置")
    print("="*80)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        if api_key and endpoint:
            print("✅ 环境变量配置正确")
            print(f"   Endpoint: {endpoint}")
        else:
            print("❌ 环境变量未配置")
            print("   请复制 .env.example 为 .env 并填入配置")
            return False
            
    except Exception as e:
        print(f"❌ 环境配置测试失败: {e}")
        return False
    
    print("\n" + "="*80)
    print("测试2: 验证依赖导入")
    print("="*80)
    
    try:
        from langchain_openai import AzureChatOpenAI
        from langgraph.graph import StateGraph
        print("✅ LangChain 和 LangGraph 导入成功")
    except Exception as e:
        print(f"❌ 依赖导入失败: {e}")
        return False
    
    print("\n" + "="*80)
    print("测试3: 验证工具导入")
    print("="*80)
    
    try:
        from tools.equipment_depreciation_tool import EquipmentDepreciationTool
        from tools.energy_cost_tool import EnergyCostTool
        print("✅ 所有工具导入成功")
    except Exception as e:
        print(f"❌ 工具导入失败: {e}")
        return False
    
    return True


def test_agent_run():
    """测试Agent运行（需要有效的Azure OpenAI配置）"""
    print("\n" + "="*80)
    print("测试4: 运行 Agent 进行成本估算")
    print("="*80)
    
    try:
        from agent import run_agent
        
        print("\n正在估算工艺成本...")
        result = run_agent(
            query="估算 melting 工艺的价格",
            production_volume=1_100_000,
            location="Ningbo, Zhejiang"
        )
        
        if result and 'processes' in result:
            print("\n✅ Agent 运行成功！")
            print("\n成本报告摘要：")
            for process, costs in result.get('processes', {}).items():
                if isinstance(costs, dict) and 'total' in costs:
                    print(f"  {process}: {costs['total']:.2f} CNY/kg")
            return True
        else:
            print("❌ Agent 返回结果格式错误")
            return False
            
    except Exception as e:
        print(f"❌ Agent 运行失败: {e}")
        print("\n可能的原因：")
        print("  1. Azure OpenAI 配置不正确")
        print("  2. API 密钥已过期")
        print("  3. 网络连接问题")
        return False


if __name__ == "__main__":
    print("\n🚀 开始系统测试...\n")
    
    # 运行基本测试
    basic_ok = test_basic()
    
    if basic_ok:
        # 询问是否运行Agent测试（需要API调用）
        print("\n" + "="*80)
        response = input("是否运行 Agent 测试（需要消耗 API 配额）？[y/N]: ")
        if response.lower() == 'y':
            test_agent_run()
        else:
            print("跳过 Agent 测试")
    
    print("\n" + "="*80)
    print("测试完成！")
    print("="*80)
    
    if basic_ok:
        print("\n✅ 基本配置正确，系统已就绪")
        print("\n下一步：")
        print("  1. 运行完整测试: python tests/test_agent.py")
        print("  2. 查看使用指南: docs/USAGE_GUIDE.md")
        print("  3. 开始使用 Agent: python agent.py")
    else:
        print("\n❌ 基本配置有问题，请先解决")
        print("\n参考文档：")
        print("  - README.md")
        print("  - docs/USAGE_GUIDE.md")

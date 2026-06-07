"""
图表自动生成脚本测试
"""

import json
import sys
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import pytest


class TestGenerateCharts:
    """图表生成测试类"""
    
    def test_financial_dashboard(self):
        """测试财务指标仪表盘"""
        from generate_charts import generate_financial_dashboard
        
        data = {
            "revenue": 320,
            "profit": 84.76,
            "margin": 68.72,
            "roe": 15.2
        }
        
        chart = generate_financial_dashboard(data)
        
        assert "320亿" in chart
        assert "84.76亿" in chart
        assert "68.7%" in chart
        assert "15.2%" in chart
        assert "关键财务指标一览" in chart
    
    def test_valuation_chart(self):
        """测试估值区间图"""
        from generate_charts import generate_valuation_chart
        
        data = {
            "conservative": 23.5,
            "neutral": 33.2,
            "optimistic": 42.4,
            "current": 29.45
        }
        
        chart = generate_valuation_chart(data)
        
        assert "23.5元" in chart
        assert "33.2元" in chart
        assert "42.4元" in chart
        assert "29.45元" in chart
    
    def test_technical_dashboard(self):
        """测试技术信号评估仪表盘"""
        from generate_charts import generate_technical_dashboard
        
        data = {
            "boll_position": 31.43,
            "rsi": 27.44,
            "macd": "bearish",
            "ma": "bearish"
        }
        
        chart = generate_technical_dashboard(data)
        
        assert "技术信号综合评估" in chart
        assert "七轨布林线" in chart
        assert "RSI" in chart
        assert "MACD" in chart
        assert "均线" in chart
    
    def test_consensus_chart(self):
        """测试一致预期分布图"""
        from generate_charts import generate_consensus_chart
        
        data = {
            "buy": 8,
            "hold": 2,
            "sell": 0,
            "target_prices": [35, 40, 43, 45, 48]
        }
        
        chart = generate_consensus_chart(data)
        
        assert "80%" in chart
        assert "20%" in chart
        assert "43.0元" in chart  # 中位数
    
    def test_cycle_dashboard(self):
        """测试周期定位仪表盘"""
        from generate_charts import generate_cycle_dashboard
        
        data = {
            "cycle": "复苏",
            "interest_rate": "宽松",
            "inflation": "温和",
            "liquidity": "充裕"
        }
        
        chart = generate_cycle_dashboard(data)
        
        assert "宏观周期定位仪表盘" in chart
        assert "复苏" in chart
        assert "宽松" in chart
        assert "温和" in chart
        assert "充裕" in chart
    
    def test_consensus_chart_no_data(self):
        """测试无数据的一致预期图"""
        from generate_charts import generate_consensus_chart
        
        data = {
            "buy": 0,
            "hold": 0,
            "sell": 0,
            "target_prices": []
        }
        
        chart = generate_consensus_chart(data)
        
        assert "无评级数据" in chart


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


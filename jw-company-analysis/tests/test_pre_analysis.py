#!/usr/bin/env python3
"""
pre_analysis.py 测试
测试数据处理和评分逻辑（mock 外部依赖）
"""

import pytest
import json
import sys
import os
import importlib.util
from unittest.mock import patch, MagicMock

# 动态导入模块
def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')
pre_module = load_module_from_path('pre_analysis', os.path.join(SCRIPTS_DIR, 'pre_analysis.py'))


class TestScoreCalculation:
    """测试评分计算逻辑"""

    def test_financial_score_roe_high(self):
        """高 ROE 应该得到高分"""
        data = {
            'sources': {
                'financial': {
                    'roe': 25.0,
                    'revenue': 1000,
                    'net_profit': 250,
                    'gross_margin': 45.0,
                    'net_margin': 25.0,
                    'revenue_growth': 20.0,
                    'profit_growth': 25.0,
                }
            }
        }
        result = pre_module.step1_quality_basic(data)
        # ROE > 20 应该给 20 分
        assert result['scores']['1.2_护城河'] == 20

    def test_financial_score_roe_medium(self):
        """中等 ROE 应该得到中等分"""
        data = {
            'sources': {
                'financial': {
                    'roe': 16.0,  # > 15 但 <= 20
                    'revenue': 1000,
                    'net_profit': 160,
                }
            }
        }
        result = pre_module.step1_quality_basic(data)
        assert result['scores']['1.2_护城河'] == 17

    def test_financial_score_roe_low(self):
        """低 ROE 应该得到低分"""
        data = {
            'sources': {
                'financial': {
                    'roe': 5.0,
                    'revenue': 1000,
                    'net_profit': 50,
                }
            }
        }
        result = pre_module.step1_quality_basic(data)
        assert result['scores']['1.2_护城河'] == 12

    def test_growth_score_high(self):
        """高增长应该得到高分"""
        data = {
            'sources': {
                'financial': {
                    'revenue_growth': 30.0,
                }
            }
        }
        result = pre_module.step1_quality_basic(data)
        assert result['scores']['1.4_成长性'] == 20

    def test_growth_score_negative(self):
        """负增长应该得到低分"""
        data = {
            'sources': {
                'financial': {
                    'revenue_growth': -10.0,
                }
            }
        }
        result = pre_module.step1_quality_basic(data)
        assert result['scores']['1.4_成长性'] == 8

    def test_manager_score_default(self):
        """管理层评分默认 15 分"""
        data = {'sources': {}}
        result = pre_module.step1_quality_basic(data)
        assert result['scores']['1.3_管理层'] == 15

    def test_business_model_score_with_data(self):
        """有数据时商业模式评分 18 分"""
        data = {
            'sources': {
                'financial': {
                    'revenue': 1000,
                    'net_profit': 100,
                }
            }
        }
        result = pre_module.step1_quality_basic(data)
        assert result['scores']['1.1_商业模式'] == 18

    def test_business_model_score_no_data(self):
        """无数据时商业模式评分 15 分"""
        data = {'sources': {}}
        result = pre_module.step1_quality_basic(data)
        assert result['scores']['1.1_商业模式'] == 15


class TestFinancialBasic:
    """测试财务健康度基础评分"""

    def test_debt_ratio_low(self):
        """低负债率应该得到高分"""
        data = {
            'sources': {
                'financial': {
                    'debt_ratio': 25.0,
                    'revenue_growth': 10.0,
                }
            }
        }
        result = pre_module.step2_financial_basic(data)
        assert result['scores']['2.2_资产负债表'] == 20

    def test_debt_ratio_medium(self):
        """中等负债率应该得到中等分"""
        data = {
            'sources': {
                'financial': {
                    'debt_ratio': 45.0,
                    'revenue_growth': 10.0,
                }
            }
        }
        result = pre_module.step2_financial_basic(data)
        assert result['scores']['2.2_资产负债表'] == 16

    def test_debt_ratio_high(self):
        """高负债率应该得到低分"""
        data = {
            'sources': {
                'financial': {
                    'debt_ratio': 75.0,
                    'revenue_growth': 10.0,
                }
            }
        }
        result = pre_module.step2_financial_basic(data)
        assert result['scores']['2.2_资产负债表'] == 8

    def test_growth_score_mapping(self):
        """增长评分映射测试"""
        test_cases = [
            (20.0, 18),  # > 15%
            (10.0, 14),  # > 5%
            (3.0, 11),   # > 0%
            (-5.0, 10),  # <= 0%
        ]
        for growth, expected_score in test_cases:
            data = {
                'sources': {
                    'financial': {
                        'revenue_growth': growth,
                    }
                }
            }
            result = pre_module.step2_financial_basic(data)
            assert result['scores']['2.4_财务趋势'] == expected_score, \
                f"growth={growth}, expected={expected_score}, got={result['scores']['2.4_财务趋势']}"


class TestTotalScore:
    """测试总分计算"""

    def test_total_score_range(self):
        """总分应该在 0-100 范围内"""
        data = {
            'sources': {
                'financial': {
                    'roe': 20.0,
                    'revenue': 1000,
                    'net_profit': 200,
                    'revenue_growth': 15.0,
                }
            }
        }
        result = pre_module.step1_quality_basic(data)
        assert 0 <= result['total'] <= 100
        assert result['max'] == 100

    def test_data_gaps_populated(self):
        """数据缺口应该被正确记录"""
        data = {'sources': {}}
        result = pre_module.step1_quality_basic(data)
        assert isinstance(result['data_gaps'], list)
        assert len(result['data_gaps']) > 0  # 应该有管理层数据缺口


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

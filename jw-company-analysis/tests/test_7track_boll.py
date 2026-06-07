#!/usr/bin/env python3
"""
七轨布林线计算测试
测试 calc_7track_boll 和 analyze_7track_boll 函数
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os
import importlib.util

# 动态导入以数字开头的模块
def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# 加载 7track_boll 模块
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')
boll_module = load_module_from_path('seven_track_boll', os.path.join(SCRIPTS_DIR, '7track_boll.py'))

calc_7track_boll = boll_module.calc_7track_boll
get_current_track = boll_module.get_current_track
analyze_7track_boll = boll_module.analyze_7track_boll


class TestCalc7TrackBoll:
    """测试七轨布林线计算函数"""

    def test_basic_calculation(self):
        """测试基本计算逻辑"""
        data = {
            'close': [100 + i * 0.5 for i in range(30)]
        }
        df = pd.DataFrame(data)

        result = calc_7track_boll(df, n=20, k=5)

        expected_cols = ['boll', 'top', 'track1', 'track2', 'track4', 'track5', 'bottom']
        for col in expected_cols:
            assert col in result.columns, f"缺少列: {col}"

        last_row = result.iloc[-1]
        assert last_row['top'] > last_row['track1'], "top 应大于 track1"
        assert last_row['track1'] > last_row['track2'], "track1 应大于 track2"
        assert last_row['track2'] > last_row['boll'], "track2 应大于 boll"
        assert last_row['boll'] > last_row['track4'], "boll 应大于 track4"
        assert last_row['track4'] > last_row['track5'], "track4 应大于 track5"
        assert last_row['track5'] > last_row['bottom'], "track5 应大于 bottom"

    def test_boll_is_20day_ma(self):
        """验证中轨是 20 日均线"""
        data = {'close': [100] * 25}
        df = pd.DataFrame(data)

        result = calc_7track_boll(df, n=20, k=5)

        assert abs(result.iloc[-1]['boll'] - 100) < 0.01, f"boll={result.iloc[-1]['boll']}, 期望接近 100"

    def test_constant_price_zero_std(self):
        """恒定价格时标准差为 0，轨道应等于中轨"""
        data = {'close': [50.0] * 30}
        df = pd.DataFrame(data)

        result = calc_7track_boll(df, n=20, k=5)

        last_row = result.iloc[-1]
        for col in ['top', 'track1', 'track2', 'track4', 'track5', 'bottom']:
            assert abs(last_row[col] - last_row['boll']) < 0.01, \
                f"{col}={last_row[col]}, boll={last_row['boll']}, 恒定价格时应相等"

    def test_nan_for_insufficient_data(self):
        """数据不足时应返回 NaN"""
        data = {'close': [100] * 5}
        df = pd.DataFrame(data)

        result = calc_7track_boll(df, n=20, k=5)

        # 前 19 天的 boll 应该是 NaN
        assert pd.isna(result['boll'].iloc[0]), "前 19 天 boll 应为 NaN"


class TestGetCurrentTrack:
    """测试当前轨道判断函数"""

    def test_top_track(self):
        row = pd.Series({'close': 110, 'top': 105, 'track1': 100, 'track2': 95,
                         'boll': 90, 'track4': 85, 'track5': 80, 'bottom': 75})
        assert get_current_track(row) == '顶轨 (极度超买)'

    def test_track1(self):
        row = pd.Series({'close': 102, 'top': 105, 'track1': 100, 'track2': 95,
                         'boll': 90, 'track4': 85, 'track5': 80, 'bottom': 75})
        assert get_current_track(row) == '一轨 (超买)'

    def test_boll_track(self):
        row = pd.Series({'close': 92, 'top': 105, 'track1': 100, 'track2': 95,
                         'boll': 90, 'track4': 85, 'track5': 80, 'bottom': 75})
        assert get_current_track(row) == 'BOLL (中轨)'

    def test_bottom_track(self):
        row = pd.Series({'close': 70, 'top': 105, 'track1': 100, 'track2': 95,
                         'boll': 90, 'track4': 85, 'track5': 80, 'bottom': 75})
        assert get_current_track(row) == '底轨 (极度超卖)'

    def test_nan_returns_unknown(self):
        row = pd.Series({'close': 100, 'top': float('nan'), 'track1': 100, 'track2': 95,
                         'boll': 90, 'track4': 85, 'track5': 80, 'bottom': 75})
        assert get_current_track(row) == 'unknown'


class TestAnalyze7TrackBoll:
    """测试七轨布林线分析函数"""

    def test_empty_df(self):
        df = pd.DataFrame()
        result = analyze_7track_boll(df)
        assert 'error' in result

    def test_normal_analysis(self):
        data = {'close': [100 + i * 0.1 for i in range(30)]}
        df = pd.DataFrame(data)
        df = calc_7track_boll(df, n=20, k=5)

        result = analyze_7track_boll(df)

        assert 'current_price' in result
        assert 'current_track' in result
        assert 'signals' in result
        assert isinstance(result['signals'], list)
        assert len(result['signals']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

"""
检查点管理器测试
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import pytest


class TestCheckpointManager:
    """检查点管理器测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.symbol = "TEST001"
        self.date = "20260608"
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_load_checkpoint_no_file(self):
        """测试加载不存在的检查点"""
        from checkpoint_manager import load_checkpoint
        
        # Mock检查点目录
        import checkpoint_manager
        original_dir = checkpoint_manager.CHECKPOINT_DIR
        checkpoint_manager.CHECKPOINT_DIR = Path(self.test_dir)
        
        checkpoint = load_checkpoint(self.symbol, self.date)
        
        assert checkpoint["status"] == "no_checkpoint"
        assert checkpoint["last_step"] == -1
        assert checkpoint["completed_steps"] == []
        
        checkpoint_manager.CHECKPOINT_DIR = original_dir
    
    def test_save_and_load_checkpoint(self):
        """测试保存和加载检查点"""
        from checkpoint_manager import save_checkpoint, load_checkpoint
        
        # Mock检查点目录
        import checkpoint_manager
        original_dir = checkpoint_manager.CHECKPOINT_DIR
        checkpoint_manager.CHECKPOINT_DIR = Path(self.test_dir)
        
        # 保存检查点
        checkpoint = save_checkpoint(self.symbol, 1, "/tmp/test.json", self.date)
        
        assert checkpoint["status"] == "in_progress"
        assert checkpoint["last_step"] == 1
        assert 1 in checkpoint["completed_steps"]
        assert checkpoint["output_files"]["step1"] == "/tmp/test.json"
        
        # 加载检查点
        loaded = load_checkpoint(self.symbol, self.date)
        
        assert loaded["status"] == "in_progress"
        assert loaded["last_step"] == 1
        assert 1 in loaded["completed_steps"]
        
        checkpoint_manager.CHECKPOINT_DIR = original_dir
    
    def test_restart_from_step(self):
        """测试从指定Step重新开始"""
        from checkpoint_manager import save_checkpoint, restart_from_step, load_checkpoint
        
        # Mock检查点目录
        import checkpoint_manager
        original_dir = checkpoint_manager.CHECKPOINT_DIR
        checkpoint_manager.CHECKPOINT_DIR = Path(self.test_dir)
        
        # 保存多个Step
        save_checkpoint(self.symbol, 0, "/tmp/step0.json", self.date)
        save_checkpoint(self.symbol, 1, "/tmp/step1.json", self.date)
        save_checkpoint(self.symbol, 2, "/tmp/step2.json", self.date)
        save_checkpoint(self.symbol, 3, "/tmp/step3.json", self.date)
        
        # 从Step 2重新开始
        checkpoint = restart_from_step(self.symbol, 2, self.date)
        
        assert checkpoint["last_step"] == 1
        assert 2 not in checkpoint["completed_steps"]
        assert 3 not in checkpoint["completed_steps"]
        assert "step2" not in checkpoint["output_files"]
        assert "step3" not in checkpoint["output_files"]
        
        checkpoint_manager.CHECKPOINT_DIR = original_dir
    
    def test_skip_step(self):
        """测试跳过指定Step"""
        from checkpoint_manager import save_checkpoint, skip_step, load_checkpoint
        
        # Mock检查点目录
        import checkpoint_manager
        original_dir = checkpoint_manager.CHECKPOINT_DIR
        checkpoint_manager.CHECKPOINT_DIR = Path(self.test_dir)
        
        # 保存检查点
        save_checkpoint(self.symbol, 0, "/tmp/step0.json", self.date)
        save_checkpoint(self.symbol, 1, "/tmp/step1.json", self.date)
        
        # 跳过Step 2
        checkpoint = skip_step(self.symbol, 2, self.date)
        
        assert 2 in checkpoint["completed_steps"]
        assert 2 in checkpoint["skipped_steps"]
        
        checkpoint_manager.CHECKPOINT_DIR = original_dir
    
    def test_validate_checkpoint_valid(self):
        """测试验证有效检查点"""
        from checkpoint_manager import save_checkpoint, validate_checkpoint
        
        # Mock检查点目录
        import checkpoint_manager
        original_dir = checkpoint_manager.CHECKPOINT_DIR
        checkpoint_manager.CHECKPOINT_DIR = Path(self.test_dir)
        
        # 创建临时输出文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"test": True}, f)
            temp_file = f.name
        
        try:
            # 保存检查点
            save_checkpoint(self.symbol, 0, temp_file, self.date)
            
            # 验证
            result = validate_checkpoint(self.symbol, self.date)
            
            assert result["valid"] == True
            assert len(result["issues"]) == 0
        finally:
            os.unlink(temp_file)
        
        checkpoint_manager.CHECKPOINT_DIR = original_dir
    
    def test_validate_checkpoint_missing_file(self):
        """测试验证缺失文件的检查点"""
        from checkpoint_manager import save_checkpoint, validate_checkpoint
        
        # Mock检查点目录
        import checkpoint_manager
        original_dir = checkpoint_manager.CHECKPOINT_DIR
        checkpoint_manager.CHECKPOINT_DIR = Path(self.test_dir)
        
        # 保存检查点（指向不存在的文件）
        save_checkpoint(self.symbol, 0, "/tmp/nonexistent.json", self.date)
        
        # 验证
        result = validate_checkpoint(self.symbol, self.date)
        
        assert result["valid"] == False
        assert any("不存在" in issue for issue in result["issues"])
        
        checkpoint_manager.CHECKPOINT_DIR = original_dir
    
    def test_validate_checkpoint_dependency(self):
        """测试验证依赖关系"""
        from checkpoint_manager import save_checkpoint, validate_checkpoint
        
        # Mock检查点目录
        import checkpoint_manager
        original_dir = checkpoint_manager.CHECKPOINT_DIR
        checkpoint_manager.CHECKPOINT_DIR = Path(self.test_dir)
        
        # 创建临时输出文件
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump({"step": i}, f)
                temp_files.append(f.name)
        
        try:
            # 保存检查点（跳过Step 0.5和0.6）
            save_checkpoint(self.symbol, 0, temp_files[0], self.date)
            save_checkpoint(self.symbol, 1, temp_files[1], self.date)
            
            # 验证
            result = validate_checkpoint(self.symbol, self.date)
            
            # Step 1 依赖 0, 0.5, 0.6，但0.5和0.6未完成
            assert result["valid"] == False
            assert any("依赖未满足" in issue for issue in result["issues"])
        finally:
            for f in temp_files:
                os.unlink(f)
        
        checkpoint_manager.CHECKPOINT_DIR = original_dir
    
    def test_repair_checkpoint(self):
        """测试修复检查点"""
        from checkpoint_manager import save_checkpoint, repair_checkpoint, load_checkpoint
        
        # Mock检查点目录
        import checkpoint_manager
        original_dir = checkpoint_manager.CHECKPOINT_DIR
        checkpoint_manager.CHECKPOINT_DIR = Path(self.test_dir)
        
        # 创建临时输出文件
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump({"step": i}, f)
                temp_files.append(f.name)
        
        try:
            # 保存检查点（跳过Step 0.5和0.6）
            save_checkpoint(self.symbol, 0, temp_files[0], self.date)
            save_checkpoint(self.symbol, 1, temp_files[1], self.date)
            
            # 修复
            result = repair_checkpoint(self.symbol, self.date)
            
            assert result["repaired"] == True
            assert len(result["repairs"]) > 0
            
            # 验证修复后的检查点
            checkpoint = load_checkpoint(self.symbol, self.date)
            assert 1 not in checkpoint["completed_steps"]
        finally:
            for f in temp_files:
                os.unlink(f)
        
        checkpoint_manager.CHECKPOINT_DIR = original_dir


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


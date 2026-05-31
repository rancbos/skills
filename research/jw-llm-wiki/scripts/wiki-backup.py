#!/usr/bin/env python3
"""
Wiki 备份脚本
支持本地备份和 Git 版本控制
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

def get_wiki_path():
    """获取 wiki 路径"""
    wiki_path = os.environ.get('WIKI_PATH')
    if not wiki_path:
        wiki_path = os.path.expanduser('~/wiki')
    return Path(wiki_path)

def create_backup(wiki_path, backup_dir=None):
    """创建本地备份"""
    if backup_dir is None:
        backup_dir = Path.home() / 'wiki-backups'
    
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"wiki-backup-{timestamp}.tar.gz"
    backup_path = backup_dir / backup_name
    
    print(f"📦 创建备份: {backup_path}")
    
    # 创建压缩包
    try:
        subprocess.run([
            'tar', '-czf', str(backup_path), '-C', str(wiki_path.parent), wiki_path.name
        ], check=True, capture_output=True)
        
        # 获取备份大小
        size_mb = backup_path.stat().st_size / (1024 * 1024)
        print(f"✅ 备份完成: {size_mb:.2f} MB")
        return backup_path
    except subprocess.CalledProcessError as e:
        print(f"❌ 备份失败: {e}")
        return None

def init_git(wiki_path):
    """初始化 Git 仓库"""
    git_dir = wiki_path / '.git'
    
    if git_dir.exists():
        print("ℹ️  Git 仓库已存在")
        return True
    
    try:
        subprocess.run(['git', 'init'], cwd=wiki_path, check=True, capture_output=True)
        
        # 创建 .gitignore
        gitignore_content = """
# 备份文件
*.tar.gz
*.zip

# 临时文件
*.tmp
*.swp
*~

# Obsidian 配置
.obsidian/workspace.json
.obsidian/workspace-mobile.json

# 大型原始文件（可选）
# raw/papers/*.pdf
"""
        with open(wiki_path / '.gitignore', 'w') as f:
            f.write(gitignore_content)
        
        # 初始提交
        subprocess.run(['git', 'add', '.'], cwd=wiki_path, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Initial wiki structure'], 
                      cwd=wiki_path, check=True, capture_output=True)
        
        print("✅ Git 仓库初始化完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Git 初始化失败: {e}")
        return False

def git_commit(wiki_path, message=None):
    """Git 提交"""
    if not (wiki_path / '.git').exists():
        print("❌ Git 仓库不存在，先运行 init-git")
        return False
    
    if message is None:
        message = f"Wiki update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    try:
        # 检查是否有变更
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              cwd=wiki_path, capture_output=True, text=True)
        
        if not result.stdout.strip():
            print("ℹ️  没有变更需要提交")
            return True
        
        # 添加所有变更
        subprocess.run(['git', 'add', '-A'], cwd=wiki_path, check=True, capture_output=True)
        
        # 提交
        subprocess.run(['git', 'commit', '-m', message], 
                      cwd=wiki_path, check=True, capture_output=True)
        
        print(f"✅ Git 提交完成: {message}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Git 提交失败: {e}")
        return False

def git_push(wiki_path, remote='origin', branch='main'):
    """推送到远程仓库"""
    if not (wiki_path / '.git').exists():
        print("❌ Git 仓库不存在")
        return False
    
    try:
        # 检查远程仓库
        result = subprocess.run(['git', 'remote', '-v'], 
                              cwd=wiki_path, capture_output=True, text=True)
        
        if remote not in result.stdout:
            print(f"❌ 远程仓库 '{remote}' 未配置")
            print("  运行: git remote add origin <your-repo-url>")
            return False
        
        # 推送
        subprocess.run(['git', 'push', remote, branch], 
                      cwd=wiki_path, check=True, capture_output=True)
        
        print(f"✅ 推送到 {remote}/{branch} 完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 推送失败: {e}")
        return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Wiki 备份工具')
    parser.add_argument('action', choices=['backup', 'init-git', 'commit', 'push'],
                       help='操作类型')
    parser.add_argument('--message', '-m', help='Git 提交信息')
    parser.add_argument('--remote', default='origin', help='Git 远程仓库名')
    parser.add_argument('--branch', default='main', help='Git 分支名')
    
    args = parser.parse_args()
    
    wiki_path = get_wiki_path()
    
    if not wiki_path.exists():
        print(f"❌ Wiki 目录不存在: {wiki_path}")
        sys.exit(1)
    
    if args.action == 'backup':
        create_backup(wiki_path)
    elif args.action == 'init-git':
        init_git(wiki_path)
    elif args.action == 'commit':
        git_commit(wiki_path, args.message)
    elif args.action == 'push':
        git_push(wiki_path, args.remote, args.branch)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Wiki 健康检查脚本
用于验证 wiki 结构、内容和一致性
"""

import os
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict

def get_wiki_path():
    """获取 wiki 路径"""
    wiki_path = os.environ.get('WIKI_PATH')
    if not wiki_path:
        wiki_path = os.path.expanduser('~/wiki')
    return Path(wiki_path)

def check_structure(wiki_path):
    """检查目录结构"""
    issues = []
    required_dirs = ['raw', 'entities', 'concepts', 'comparisons', 'queries']
    required_files = ['SCHEMA.md', 'index.md', 'log.md']
    
    for d in required_dirs:
        if not (wiki_path / d).exists():
            issues.append(f"缺失目录: {d}")
    
    for f in required_files:
        if not (wiki_path / f).exists():
            issues.append(f"缺失文件: {f}")
    
    return issues

def extract_frontmatter(filepath):
    """提取 YAML frontmatter"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.startswith('---'):
            return None
        
        # 找到第二个 ---
        end_match = re.search(r'\n---\s*\n', content[3:])
        if not end_match:
            return None
        
        frontmatter_text = content[4:end_match.start() + 3]
        
        # 简单解析 YAML
        result = {}
        for line in frontmatter_text.split('\n'):
            line = line.strip()
            if ':' in line and not line.startswith('#'):
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # 处理列表
                if value.startswith('[') and value.endswith(']'):
                    value = [v.strip().strip('"\'') for v in value[1:-1].split(',')]
                elif value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                result[key] = value
        
        return result
    except Exception as e:
        return {'error': str(e)}

def check_frontmatter(filepath, schema_tags=None):
    """检查 frontmatter 完整性"""
    issues = []
    frontmatter = extract_frontmatter(filepath)
    
    if frontmatter is None:
        issues.append("缺失 frontmatter")
        return issues
    
    if 'error' in frontmatter:
        issues.append(f"frontmatter 解析错误: {frontmatter['error']}")
        return issues
    
    # 必需字段
    required_fields = ['title', 'created', 'updated', 'type', 'tags', 'sources']
    for field in required_fields:
        if field not in frontmatter:
            issues.append(f"缺失必需字段: {field}")
    
    # 检查标签
    if 'tags' in frontmatter and schema_tags:
        tags = frontmatter['tags']
        if isinstance(tags, list):
            for tag in tags:
                if tag not in schema_tags:
                    issues.append(f"未分类标签: {tag}")
    
    return issues

def find_orphan_pages(wiki_path):
    """查找孤儿页面（无入链）"""
    # 收集所有页面
    all_pages = set()
    page_files = {}
    
    for md_file in wiki_path.rglob('*.md'):
        if md_file.name.startswith('SCHEMA') or md_file.name.startswith('index') or md_file.name.startswith('log'):
            continue
        
        rel_path = md_file.relative_to(wiki_path)
        page_name = md_file.stem
        all_pages.add(page_name)
        page_files[page_name] = rel_path
    
    # 收集所有链接
    linked_pages = set()
    link_pattern = re.compile(r'\[\[([^\]]+)\]\]')
    
    for md_file in wiki_path.rglob('*.md'):
        if md_file.name.startswith('SCHEMA') or md_file.name.startswith('index') or md_file.name.startswith('log'):
            continue
        
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            links = link_pattern.findall(content)
            for link in links:
                # 处理别名 [[page|alias]]
                page_name = link.split('|')[0].strip()
                linked_pages.add(page_name)
        except:
            pass
    
    # 查找孤儿
    orphan_pages = all_pages - linked_pages
    return orphan_pages, page_files

def find_broken_links(wiki_path):
    """查找断链"""
    broken_links = []
    link_pattern = re.compile(r'\[\[([^\]]+)\]\]')
    
    # 收集所有页面
    all_pages = set()
    for md_file in wiki_path.rglob('*.md'):
        if md_file.name.startswith('SCHEMA') or md_file.name.startswith('index') or md_file.name.startswith('log'):
            continue
        all_pages.add(md_file.stem)
    
    for md_file in wiki_path.rglob('*.md'):
        if md_file.name.startswith('SCHEMA') or md_file.name.startswith('index') or md_file.name.startswith('log'):
            continue
        
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            links = link_pattern.findall(content)
            for link in links:
                page_name = link.split('|')[0].strip()
                if page_name not in all_pages:
                    broken_links.append((md_file.name, page_name))
        except:
            pass
    
    return broken_links

def check_page_sizes(wiki_path, max_lines=200):
    """检查页面大小"""
    large_pages = []
    
    for md_file in wiki_path.rglob('*.md'):
        if md_file.name.startswith('SCHEMA') or md_file.name.startswith('index') or md_file.name.startswith('log'):
            continue
        
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if len(lines) > max_lines:
                large_pages.append((md_file.name, len(lines)))
        except:
            pass
    
    return large_pages

def main():
    """主函数"""
    wiki_path = get_wiki_path()
    
    if not wiki_path.exists():
        print(f"❌ Wiki 目录不存在: {wiki_path}")
        sys.exit(1)
    
    print(f"🔍 检查 Wiki: {wiki_path}")
    print("=" * 60)
    
    all_issues = []
    
    # 1. 检查目录结构
    print("\n📁 目录结构检查:")
    structure_issues = check_structure(wiki_path)
    if structure_issues:
        for issue in structure_issues:
            print(f"  ❌ {issue}")
            all_issues.append(("结构", issue))
    else:
        print("  ✅ 目录结构完整")
    
    # 2. 检查 frontmatter
    print("\n📝 Frontmatter 检查:")
    schema_tags = set()  # 简化版本，实际应从 SCHEMA.md 解析
    
    frontmatter_issues = []
    for md_file in wiki_path.rglob('*.md'):
        if md_file.name.startswith('SCHEMA') or md_file.name.startswith('index') or md_file.name.startswith('log'):
            continue
        
        issues = check_frontmatter(md_file, schema_tags)
        if issues:
            for issue in issues:
                frontmatter_issues.append((md_file.name, issue))
    
    if frontmatter_issues:
        print(f"  ⚠️  发现 {len(frontmatter_issues)} 个 frontmatter 问题")
        # 只显示前 5 个
        for filename, issue in frontmatter_issues[:5]:
            print(f"    - {filename}: {issue}")
        if len(frontmatter_issues) > 5:
            print(f"    ... 还有 {len(frontmatter_issues) - 5} 个问题")
    else:
        print("  ✅ 所有 frontmatter 完整")
    
    # 3. 检查孤儿页面
    print("\n🔗 孤儿页面检查:")
    orphan_pages, page_files = find_orphan_pages(wiki_path)
    if orphan_pages:
        print(f"  ⚠️  发现 {len(orphan_pages)} 个孤儿页面")
        for page in list(orphan_pages)[:5]:
            print(f"    - {page}")
        if len(orphan_pages) > 5:
            print(f"    ... 还有 {len(orphan_pages) - 5} 个")
    else:
        print("  ✅ 无孤儿页面")
    
    # 4. 检查断链
    print("\n🔗 断链检查:")
    broken_links = find_broken_links(wiki_path)
    if broken_links:
        print(f"  ❌ 发现 {len(broken_links)} 个断链")
        for filename, link in broken_links[:5]:
            print(f"    - {filename} → [[{link}]]")
        if len(broken_links) > 5:
            print(f"    ... 还有 {len(broken_links) - 5} 个")
    else:
        print("  ✅ 无断链")
    
    # 5. 检查页面大小
    print("\n📄 页面大小检查:")
    large_pages = check_page_sizes(wiki_path)
    if large_pages:
        print(f"  ⚠️  发现 {len(large_pages)} 个超大页面（>200行）")
        for filename, lines in large_pages[:5]:
            print(f"    - {filename}: {lines} 行")
    else:
        print("  ✅ 所有页面大小正常")
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 检查总结:")
    
    total_issues = (len(structure_issues) + len(frontmatter_issues) + 
                   len(orphan_pages) + len(broken_links) + len(large_pages))
    
    if total_issues == 0:
        print("  ✅ Wiki 状态良好，未发现问题")
    else:
        print(f"  ⚠️  共发现 {total_issues} 个问题")
        print("  建议运行详细检查或手动修复")
    
    return 0 if total_issues == 0 else 1

if __name__ == '__main__':
    sys.exit(main())

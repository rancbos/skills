#!/usr/bin/env python3
"""
ebook_ops.py -- 电子书文件操作的辅助脚本

提供八个子命令:
  scan          -- 扫描目录中的电子书（支持 --incremental 增量模式）
  clean-titles  -- 从扫描结果中清洗出干净书名
  move          -- 按分类计划移动文件（支持 --copy 复制模式）
  report        -- 生成整理报告（JSON）
  index         -- 生成 Markdown 格式的图书索引目录
  undo          -- 撤销上一次整理，恢复文件到原始位置

使用方式（由 SKILL.md 中的 WorkBuddy 调用）:
  python ebook_ops.py scan          <目录路径> [--ext ...] [--output file.json] [--incremental]
  python ebook_ops.py clean-titles  <scan_file.json> [--output file.json]
  python ebook_ops.py move          <分类计划文件.json> [--dry-run] [--copy]
  python ebook_ops.py report        <目录路径> [--output file.json]
  python ebook_ops.py index         <整理后的目录> [--output 图书索引.md]
  python ebook_ops.py undo          [manifest文件] [--dry-run]
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path


# 强制 UTF-8 编码输出，解决 Windows GBK 乱码问题
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


# 支持的电子书扩展名（小写）
DEFAULT_EXTENSIONS = {".pdf", ".epub", ".mobi", ".azw3", ".djvu", ".cbr", ".cbz"}

# CLC（中国图书馆图书分类法）关键词参考（多级展开版）
# 文件夹命名格式：代码-类名（如 F83-金融投资）
CATEGORY_KEYWORDS = {
    # B-哲学（展开子类）
    "B0-哲学理论": ["哲学理论", "哲学概论", "本体论", "认识论", "辩证法", "唯物论", "唯心论"],
    "B1-西方哲学": ["西方哲学", "亚里士多德", "柏拉图", "康德", "尼采", "黑格尔", "笛卡尔", "卢梭", "休谟", "罗素"],
    "B2-中国哲学": ["论语", "老子", "庄子", "孟子", "王阳明", "道德经", "周易", "儒家", "道家", "禅宗", "朱熹", "国学", "传习录"],
    "B80-思维科学": ["思维", "认知", "底层逻辑", "方法论", "深度思考", "心智", "模型思维", "系统思考", "批判性思维", "第一性原理"],
    "B84-心理学": ["心理", "乌合之众", "行为", "人格", "情绪", "同理心", "社会心理", "认知偏", "潜意识",
                   "自卑", "拖延", "自控", "注意力", "动机", "幸福感"],
    "B9-宗教": ["宗教", "佛教", "基督教", "伊斯兰教", "信仰", "禅", "净土", "圣经", "古兰经"],
    # C-社会科学
    "C-社会科学总论": ["社会科学", "社会学", "统计学", "社交", "沟通", "说话", "谈判", "影响力", "搭讪", "连接", "人际关系", "人类学"],
    "C93-管理学": ["管理", "领导力", "明茨伯格", "组织", "德鲁克", "管理百年", "决策", "执行力", "项目管理", "OKR"],
    # D-政治法律
    "D-政治法律": ["政治", "法律", "法治", "治理", "改革", "乡镇", "小镇", "政府", "制度", "社会主义", "宪法", "民主", "政策"],
    # F-经济（重点展开）
    "F0-经济学": ["经济学", "宏观", "微观", "曼昆", "凯恩斯", "萨缪尔森", "政治经济学", "GDP", "供给", "需求", "通胀", "通缩"],
    "F1-中国经济": ["中国经济", "林毅夫", "黄奇帆", "双循环", "现代化", "结构性", "去依附", "繁荣",
                   "刘鹤", "张五常", "解读中国", "十四五", "新发展格局"],
    "F2-经济管理": ["企业管理", "战略", "波特", "竞争", "商业模式", "价值链", "核心竞争力", "蓝海", "创业", "创新",
                   "增长", "运营", "供应链"],
    "F7-贸易": ["贸易", "进出口", "外贸", "跨境电商", "国际商务", "关税", "全球化"],
    "F81-财政金融": ["财政", "货币", "国债", "债券", "利率", "汇率", "央行", "银行", "信贷"],
    "F83-金融投资": ["巴菲特", "投资", "价值投资", "股票", "基金", "ETF", "指数", "财报", "护城河",
                    "格雷厄姆", "芒格", "林奇", "资本", "股息", "资产配置", "复利", "定投"],
    "F83-证券交易": ["K线", "交易", "价格行为", "技术分析", "外汇", "短线", "趋势", "蜡烛图",
                    "波段", "量化", "盘口", "缠论", "裸K"],
    "F84-保险": ["保险", "社保", "养老", "重疾", "寿险"],
    # G-文化教育
    "G-文化教育": ["文化", "教育", "学习", "传媒", "信息", "知识", "阅读", "写作", "教学", "出版", "文献"],
    # H-语言文字
    "H-语言文字": ["语言", "汉语", "英语", "语法", "修辞", "翻译", "方言", "文字", "词汇", "写作"],
    # I-文学（展开子类）
    "I24-小说": ["小说", "三体", "追风筝", "围城", "活着", "红楼梦", "百年孤独", "科幻", "武侠", "推理", "悬疑"],
    "I26-散文": ["散文", "随笔", "杂文", "瓦尔登湖", "朝花夕拾"],
    "I-文学": ["诗歌", "诗词", "文学理论", "戏剧", "剧本", "文学史"],
    # K-历史地理（展开子类）
    "K0-史学理论": ["史学", "历史哲学", "历史研究", "史料", "编年"],
    "K1-世界史": ["世界史", "欧洲史", "美国史", "日本史", "全球史", "文明"],
    "K2-中国史": ["中国史", "中国历史", "中国近代史", "革命", "八次危机", "制度史", "古代史",
                  "民国", "改革开放", "历史文化"],
    "K81-传记": ["传记", "自传", "回忆录", "乔布斯", "段永平", "传", "年谱", "生平", "口述"],
    # R-医药卫生
    "R-医药卫生": ["医学", "健康", "营养", "中医", "西医", "养生", "疾病", "药", "本草", "方剂"],
    # TP-计算机技术
    "TP-计算机技术": ["计算机", "编程", "算法", "人工智能", "数据", "软件", "Python", "Java",
                     "机器学习", "深度学习", "网络", "数据库", "操作系统", "架构"],
    # Z-综合性图书
    "Z-综合性图书": ["百科", "全书", "手册", "年鉴", "大全", "辞典", "词典", "索引"],
}


# ---------------------------------------------------------------------------
# 书名清洗
# ---------------------------------------------------------------------------

def clean_book_title(filename: str) -> str:
    """从文件名中提取干净的书籍标题（去除扩展名、作者、来源标记等噪音）"""
    name = Path(filename).stem

    # 书名号内的内容优先
    m = re.search(r'《([^》]+)》', name)
    if m:
        return m.group(1).strip()

    # 多级嵌套括号清理（最多 3 层）
    cleaned = name
    for _ in range(3):
        prev = cleaned
        cleaned = re.sub(r'[（(][^（）()]{0,80}(?:来源|Z[- ]?[Ll]ib|[Ll]ibrary|'
                         r'高清|完整图文版|典藏版|珍藏版|增订版|修订版|'
                         r'原书第\d版|第\d版|图文版|202\d版|'
                         r'著|译|编|主编|编著|编译|选编|选|整理|校注|校|'
                         r'套装[共全]\s*\d+\s*册|全\s*\d+\s*册|簡體)[^）)]{0,60}[）)]',
                         '', prev)
        if cleaned == prev:
            break
    name = cleaned

    # 明确的来源标记（全角/半角混合写法）
    noise_patterns = [
        r'[（(][^）)]*[ZzLl][-_　 ]?[LlIi][IiBb][BbRr][RrAa][AaYy][^）)]*[）)]',
        r'[（(][^）)]*[/,]\s*[12][lL][iI][bB]\.[a-zA-Z]+\w*[^）)]*[）)]',
        r'[（(][^）)]*[zZ]-[lL][iI][bB][^）)]*[）)]',
        r'[（(][^）)]*1[lL][iI][bB][^）)]*[）)]',
        r'[（(]来源：?[^）)]*[）)]',
        r'[（(]簡體[^）)]*[）)]',
        r'[（(]套装[共全]\s*\d+\s*册[）)]',
        r'[（(]全\s*\d+\s*册[）)]',
        r'[（(]图文版[）)]',
        r'[（(]202\d[版年][）)]',
    ]
    for p in noise_patterns:
        name = re.sub(p, '', name)

    # 全角破折号 —— 前后截断（通常前半是书名，后半是作者）
    name = re.sub(r'\s*[-–—]{2,}\s*[\u4e00-\u9fff·\.\s]{1,30}$', '', name)
    # 半角/全角混合分隔
    name = re.sub(r'\s*[-–—]+\s*[\u4e00-\u9fff·\.\s]{1,20}$', '', name)

    # 尾部 "by Author"
    name = re.sub(r'\s+[Bb][Yy]\s+[a-zA-Z\u4e00-\u9fff\.\s]{1,30}$', '', name)

    # 尾部残留括号（孤立的 (作者名) 或（作者名））
    name = re.sub(r'\s*[（(][\u4e00-\u9fff·\.a-zA-Z\s]{1,20}[）)]\s*$', '', name)

    # 去掉 【】 或 [] 内的内容（出版社标记等）
    name = re.sub(r'[【\[]([^】\]]){1,40}[】\]]', '', name)

    # 去掉英文引号包裹的字母残留
    name = name.replace('"', '').replace("'", '')

    # 清理头尾噪音字符
    name = name.strip()
    name = re.sub(r'^[-–—\s\u3000]+', '', name)
    name = re.sub(r'[-–—\s\u3000]+$', '', name)

    # 压缩中间多余空格（含全角空格）
    name = re.sub(r'\s{2,}', ' ', name)
    name = re.sub(r'\u3000', '', name)

    # 去掉头尾括号残片
    name = re.sub(r'^[（(]', '', name)
    name = re.sub(r'[）)]$', '', name)

    # 去掉孤立的 . - —— 等符号
    name = name.strip('-_–—.\u3000 ')

    return name if name else Path(filename).stem


def clean_titles(scan_file: str) -> dict:
    """读取 scan_result.json 并给每个文件添加 clean_title 字段"""
    if not os.path.exists(scan_file):
        return {"error": "扫描结果文件不存在: " + scan_file}
    with open(scan_file, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    files = data.get("files", [])
    for f in files:
        f["clean_title"] = clean_book_title(f.get("filename", ""))
    data["cleaned"] = True
    data["file_count"] = len(files)
    return data


# ---------------------------------------------------------------------------
# 扫描
# ---------------------------------------------------------------------------

def scan_directory(target_dir: str, extensions: set) -> list:
    """递归扫描目录，返回电子书文件信息列表"""
    target = Path(target_dir)
    if not target.exists():
        print(json.dumps({"error": "目录不存在: " + target_dir}))
        sys.exit(1)

    # 需要跳过的后缀（--copy 产生的标记文件）
    SKIP_SUFFIXES = (".source", ".tmp", ".bak")

    results = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for fname in sorted(files):
            ext = Path(fname).suffix.lower()
            # 跳过标记文件
            if any(fname.lower().endswith(s) for s in SKIP_SUFFIXES):
                continue
            if ext in extensions:
                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, target)
                size_bytes = os.path.getsize(full_path)
                results.append({
                    "filename": fname,
                    "extension": ext,
                    "relative_path": rel_path,
                    "absolute_path": full_path,
                    "size_bytes": size_bytes,
                    "size_mb": round(size_bytes / 1024 / 1024, 2),
                    "parent_folder": os.path.basename(root),
                })
    return results


# ---------------------------------------------------------------------------
# 移动文件
# ---------------------------------------------------------------------------

def move_files(plan_file: str, dry_run: bool = False, copy_mode: bool = False) -> dict:
    """根据分类计划移动/重命名电子书。
    
    特性：
    1. 多格式合并：同一书名有 2+ 文件（不同格式）→ 放入 {书名-作者}/ 子文件夹
    2. 作者归档：同作者 2+ 本书 → 放入 {作者}/ 子文件夹
    3. 去重：同一目标路径 + 文件大小相同 → 跳过
    4. 加后缀：同一目标路径 + 文件大小不同 → 加 _1/_2
    5. 复制模式：--copy 先复制，源文件改 .source 后缀
    """
    from collections import defaultdict as dd

    if not os.path.exists(plan_file):
        return {"error": "计划文件不存在: " + plan_file}

    with open(plan_file, "r", encoding="utf-8-sig") as f:
        plan = json.load(f)

    stats = {
        "total_files": 0, "moved": 0,
        "skipped_duplicate": 0, "errors": 0,
        "categories": {}, "details": [],
        "manifest": [],
    }

    if "target_directory" not in plan or "categories" not in plan:
        return {"error": "计划文件格式错误，需要 target_directory 和 categories 字段"}

    target_base = Path(plan["target_directory"])
    manifest_entries = []

    for cat_name, files in plan["categories"].items():
        cat_dir = target_base / cat_name

        # ---- Step A: 统计作者频次（决定哪些作者需要子文件夹） ----
        author_count = dd(int)
        for fi in files:
            a = (fi.get("author") or "").strip()
            if a:
                author_count[a] += 1

        # ---- Step B: 统计书名频次（决定哪些书需要多格式子文件夹） ----
        title_count = dd(int)
        for fi in files:
            t = (fi.get("clean_title") or "").strip()
            if t:
                title_count[t] += 1

        # ---- Step C: 跟踪已用目标路径 ----
        used_targets = {}
        stats["categories"][cat_name] = {"count": 0, "files": []}

        for file_info in files:
            stats["total_files"] += 1
            src = file_info.get("absolute_path") or file_info.get("source_path")
            if not src:
                stats["errors"] += 1
                continue

            src_path = Path(src)
            if not src_path.exists():
                stats["errors"] += 1
                stats["details"].append({"file": src, "status": "源文件不存在"})
                continue

            # 1. 确定目标文件名
            target_name = file_info.get("target_filename") or src_path.name
            book_title = (file_info.get("clean_title") or "").strip()
            author = (file_info.get("author") or "").strip()

            # 2. 构建路径层级
            dest = cat_dir  # 起点

            # 2a. 作者子文件夹（同一作者 2+ 本书）
            if author and author_count.get(author, 0) > 1:
                dest = dest / author

            # 2b. 书籍子文件夹（同一书名 2+ 文件 = 多格式）
            if book_title and title_count.get(book_title, 0) > 1:
                # 书籍文件夹名 = 书名-作者
                book_folder = book_title
                if author:
                    book_folder = book_title + "-" + author
                dest = dest / book_folder

            # 最终目标路径
            dest = dest / target_name
            dest_str = str(dest)
            curr_size = src_path.stat().st_size

            # 3. 去重 & 冲突处理
            if dest_str in used_targets:
                prev = used_targets[dest_str]
                if abs(curr_size - prev["size"]) < 100:
                    stats["skipped_duplicate"] += 1
                    stats["details"].append({
                        "file": str(src), "to": dest_str,
                        "status": "DUPLICATE_SAME_SIZE",
                        "kept_src": prev["src"]
                    })
                    continue
                else:
                    p = dest; stem_p = p.stem; suff_p = p.suffix; c = 1
                    while True:
                        cand = p.parent / f"{stem_p}_{c}{suff_p}"
                        if str(cand) not in used_targets:
                            dest = cand; dest_str = str(dest); break
                        c += 1

            used_targets[dest_str] = {"size": curr_size, "src": str(src)}

            # 4. 执行
            is_dry = dry_run
            if is_dry:
                stats["moved"] += 1
                stats["categories"][cat_name]["count"] += 1
                stats["categories"][cat_name]["files"].append(dest_str)
                stats["details"].append({"file": str(src), "to": dest_str, "status": "DRY_RUN"})
                manifest_entries.append({"from": str(src), "to": dest_str, "size": curr_size})
            else:
                try:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if copy_mode:
                        shutil.copy2(str(src_path), str(dest))
                        # 源文件改名标记
                        src_mark = str(src_path) + ".source"
                        os.rename(str(src_path), src_mark)
                        act = "COPIED_SOURCE_MARKED"
                    else:
                        shutil.move(str(src_path), str(dest))
                        act = "MOVED"
                    stats["moved"] += 1
                    stats["categories"][cat_name]["count"] += 1
                    stats["categories"][cat_name]["files"].append(dest_str)
                    stats["details"].append({"file": str(src), "to": dest_str, "status": act})
                    manifest_entries.append({"from": str(src), "to": dest_str, "size": curr_size, "copy_mode": copy_mode})
                except Exception as e:
                    stats["errors"] += 1
                    stats["details"].append({"file": str(src), "status": "失败: " + str(e)})

    # 保存 manifest
    if not dry_run and manifest_entries:
        manifest = {
            "timestamp": datetime.now().isoformat(),
            "target_directory": str(target_base),
            "plan_file": os.path.abspath(plan_file),
            "entries": manifest_entries,
        }
        manifest_path = target_base / ".move_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        stats["manifest_path"] = str(manifest_path)

    stats["dry_run"] = dry_run
    stats["total_unique"] = stats["moved"]
    return stats

def generate_report(target_dir: str) -> dict:
    """生成当前目录的整理状态报告"""
    files = scan_directory(target_dir, DEFAULT_EXTENSIONS)

    # 按父文件夹分组统计
    folders = {}
    for f in files:
        parent = f.get("parent_folder", "根目录")
        if parent not in folders:
            folders[parent] = {"count": 0, "total_mb": 0, "formats": set()}
        folders[parent]["count"] += 1
        folders[parent]["total_mb"] += f["size_mb"]
        folders[parent]["formats"].add(f["extension"])

    report = {
        "扫描目录": target_dir,
        "扫描时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "文件总数": len(files),
        "总大小_MB": round(sum(f["size_mb"] for f in files), 2),
        "格式分布": {},
        "文件夹分布": {},
    }

    format_counts = {}
    for f in files:
        ext = f["extension"]
        format_counts[ext] = format_counts.get(ext, 0) + 1
    report["格式分布"] = format_counts

    for folder, info in sorted(folders.items()):
        report["文件夹分布"][folder] = {
            "文件数": info["count"],
            "大小_MB": round(info["total_mb"], 2),
            "格式": sorted(info["formats"]),
        }

    return report


# ---------------------------------------------------------------------------
# 索引（Markdown 目录）
# ---------------------------------------------------------------------------

def _parse_index_name(stem: str) -> dict:
    """从文件名中解析出 书名、国籍、作者。
    
    支持的格式（按优先级）:
      书名-国籍·作者        → 聪明的投资者-美国·本杰明·格雷厄姆
      书名-国籍·作者_数字    → 聪明的投资者-美国·本杰明·格雷厄姆_1
      单纯书名               → 聪明的投资者
    """
    title = stem
    nationality = ""
    author = ""

    # 去掉末尾的 _数字 后缀（去重产生）
    clean_stem = re.sub(r'_\d+$', '', stem)

    # 尝试用最后一个 - 分隔，检查后半段是否含 ·
    parts = clean_stem.rsplit('-', 1)
    if len(parts) == 2 and '·' in parts[1]:
        title = parts[0]
        rest = parts[1]
        na = rest.split('·', 1)
        if len(na) == 2:
            nationality = na[0]
            author = na[1]

    return {
        "title": title,
        "nationality": nationality,
        "author": author,
    }


def generate_index(target_dir: str) -> str:
    """扫描已整理的目录，生成 Markdown 格式的电子书索引"""
    target = Path(target_dir)
    if not target.exists():
        return "错误：目录不存在: " + target_dir

    ebook_files = scan_directory(target_dir, DEFAULT_EXTENSIONS)
    if not ebook_files:
        return "# 📚 电子书索引\n\n该目录下没有找到电子书文件。"

    # 按父文件夹分组（CLC 分类）
    from collections import defaultdict
    groups = defaultdict(list)

    for f in ebook_files:
        path_str = f["relative_path"]
        parts = path_str.replace("\\", "/").split("/")
        # 顶层文件夹 = CLC 分类名
        # 如果有2层（分类/作者/文件），则中间层是作者子文件夹
        clc_folder = parts[0] if len(parts) >= 2 else "根目录"
        f["clc_folder"] = clc_folder
        f["author_subfolder"] = parts[1] if len(parts) >= 3 else ""
        groups[clc_folder].append(f)

    # 统计
    total_files = len(ebook_files)
    total_mb = round(sum(f["size_mb"] for f in ebook_files), 1)
    clc_list = sorted(groups.keys())
    clc_count = len(clc_list)

    # 格式化
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# 电子书索引",
        "",
        f"> 生成时间: {now_str}  |  总藏书: {total_files} 本  |  总大小: {total_mb} MB  |  覆盖 {clc_count} 个分类",
        "",
        "---",
        "",
    ]

    for clc in clc_list:
        files = groups[clc]
        clc_size = round(sum(f["size_mb"] for f in files), 1)
        lines.append(f"## {clc}  ({len(files)} 本 / {clc_size} MB)")
        lines.append("")

        # 检查是否有作者子文件夹
        author_subdirs = set(f["author_subfolder"] for f in files if f["author_subfolder"])

        if author_subdirs:
            # 先列作者子文件夹内的书
            for auth_dir in sorted(author_subdirs):
                subfiles = [f for f in files if f["author_subfolder"] == auth_dir]
                sub_size = round(sum(f["size_mb"] for f in subfiles), 1)
                lines.append(f"### {auth_dir}  ({len(subfiles)} 本 / {sub_size} MB)")
                lines.append("")
                lines.append("| # | 书名 | 格式 | 大小 |")
                lines.append("|---|------|------|------|")
                for i, f in enumerate(subfiles, 1):
                    meta = _parse_index_name(Path(f["filename"]).stem)
                    lines.append(
                        f"| {i} | {meta['title']} | {f['extension'].lstrip('.')} | {f['size_mb']} MB |"
                    )
                lines.append("")

            # 再列根目录下（不在作者子文件夹中）的书
            root_files = [f for f in files if not f["author_subfolder"]]
            if root_files:
                root_size = round(sum(f["size_mb"] for f in root_files), 1)
                lines.append(f"### (根目录)  ({len(root_files)} 本 / {root_size} MB)")
                lines.append("")
                lines.append("| # | 书名 | 作者 | 格式 | 大小 |")
                lines.append("|---|------|------|------|------|")
                for i, f in enumerate(root_files, 1):
                    meta = _parse_index_name(Path(f["filename"]).stem)
                    auth_display = f"{meta['author']}({meta['nationality']})" if meta['author'] and meta['nationality'] else (meta['author'] or "-")
                    lines.append(
                        f"| {i} | {meta['title']} | {auth_display} | {f['extension'].lstrip('.')} | {f['size_mb']} MB |"
                    )
                lines.append("")
        else:
            # 没有作者子文件夹，平铺显示
            lines.append("| # | 书名 | 作者 | 格式 | 大小 |")
            lines.append("|---|------|------|------|------|")
            for i, f in enumerate(files, 1):
                meta = _parse_index_name(Path(f["filename"]).stem)
                auth_display = f"{meta['author']}({meta['nationality']})" if meta['author'] and meta['nationality'] else (meta['author'] or "-")
                lines.append(
                    f"| {i} | {meta['title']} | {auth_display} | {f['extension'].lstrip('.')} | {f['size_mb']} MB |"
                )
            lines.append("")

        lines.append("---")
        lines.append("")

    # 附录：格式统计
    lines.append("## 附录：格式分布")
    lines.append("")
    fmt_count = defaultdict(int)
    for f in ebook_files:
        fmt_count[f["extension"]] += 1
    lines.append("| 格式 | 数量 |")
    lines.append("|------|------|")
    for ext, cnt in sorted(fmt_count.items()):
        lines.append(f"| {ext.lstrip('.')} | {cnt} |")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 撤销
# ---------------------------------------------------------------------------

def undo_move(manifest_file: str = None, dry_run: bool = False) -> dict:
    """撤销上一次整理，根据 manifest 将文件恢复到原始位置"""
    stats = {"restored": 0, "errors": 0, "details": []}

    # 查找 manifest
    if not manifest_file:
        candidates = list(Path(".").glob("**/.move_manifest.json"))
        if not candidates:
            return {"error": "未找到 .move_manifest.json，请指定 manifest 文件路径"}
        manifest_file = str(candidates[0])
        print("使用 manifest: " + manifest_file)

    with open(manifest_file, "r", encoding="utf-8-sig") as f:
        manifest = json.load(f)

    entries = manifest.get("entries", [])
    stats["total"] = len(entries)
    copy_mode = entries[0].get("copy_mode", False) if entries else False

    for entry in reversed(entries):
        to_path = Path(entry["to"])
        from_path = Path(entry["from"])

        if not to_path.exists():
            stats["details"].append({"file": entry["to"], "status": "目标文件不存在，跳过"})
            continue

        if from_path.exists():
            # 源文件位置已有东西
            stats["details"].append({"file": entry["to"], "to": entry["from"], "status": "源位置已被占用，跳过"})
            continue

        if dry_run:
            stats["restored"] += 1
            stats["details"].append({"file": entry["to"], "to": entry["from"], "status": "DRY_RUN_UNDO"})
        else:
            try:
                to_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(to_path), str(from_path))
                stats["restored"] += 1
                stats["details"].append({"file": entry["to"], "to": entry["from"], "status": "UNDONE"})
            except Exception as e:
                stats["errors"] += 1
                stats["details"].append({"file": entry["to"], "status": "恢复失败: " + str(e)})

    # 清理空目录
    if not dry_run:
        from collections import defaultdict
        parent_dirs = defaultdict(list)
        for e in entries:
            p = Path(e["to"]).parent
            parent_dirs[str(p)].append(e)
        for dir_path in sorted(parent_dirs.keys(), reverse=True):
            d = Path(dir_path)
            if d.exists() and not any(d.iterdir()):
                try:
                    d.rmdir()
                except:
                    pass

    stats["dry_run"] = dry_run
    return stats


# ---------------------------------------------------------------------------
# 清理 --copy 产生的 .source 标记文件
# ---------------------------------------------------------------------------

def clean_source_files(target_dir: str, dry_run: bool = False) -> dict:
    """递归扫描并删除 --copy 模式产生的 .source 标记文件"""
    target = Path(target_dir)
    if not target.exists():
        return {"error": "目录不存在: " + target_dir}

    stats = {"deleted": 0, "errors": 0, "details": []}
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for fname in files:
            if fname.lower().endswith(".source"):
                full_path = os.path.join(root, fname)
                if dry_run:
                    stats["deleted"] += 1
                    stats["details"].append({"file": full_path, "status": "DRY_RUN_DELETE"})
                else:
                    try:
                        os.remove(full_path)
                        stats["deleted"] += 1
                        stats["details"].append({"file": full_path, "status": "DELETED"})
                    except Exception as e:
                        stats["errors"] += 1
                        stats["details"].append({"file": full_path, "status": "删除失败: " + str(e)})
    stats["dry_run"] = dry_run
    return stats


# ---------------------------------------------------------------------------
# 增量扫描
# ---------------------------------------------------------------------------

def scan_incremental(target_dir: str, extensions: set) -> dict:
    """增量扫描：只返回新增/变更的文件"""
    state_file = Path(target_dir) / ".library_state.json"
    new_files = scan_directory(target_dir, extensions)

    if not state_file.exists():
        # 首次全量，保存状态
        state = {}
        for f in new_files:
            key = f["relative_path"]
            state[key] = {"size": f["size_bytes"], "mtime": os.path.getmtime(f["absolute_path"])}
        with open(state_file, "w", encoding="utf-8") as fp:
            json.dump(state, fp, ensure_ascii=False, indent=2)
        return {"incremental": False, "new_count": len(new_files), "files": new_files}

    with open(state_file, "r", encoding="utf-8-sig") as fp:
        old_state = json.load(fp)

    changed = []
    current_state = {}
    for f in new_files:
        key = f["relative_path"]
        mtime = os.path.getmtime(f["absolute_path"])
        current_state[key] = {"size": f["size_bytes"], "mtime": mtime}
        if key not in old_state:
            changed.append(f)
        elif old_state[key]["size"] != f["size_bytes"] or abs(old_state[key]["mtime"] - mtime) > 1:
            changed.append(f)

    # 保存新状态
    with open(state_file, "w", encoding="utf-8") as fp:
        json.dump(current_state, fp, ensure_ascii=False, indent=2)

    return {"incremental": True, "new_count": len(changed), "files": changed}


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="电子书文件操作助手")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # scan
    scan_parser = subparsers.add_parser("scan", help="扫描目录中的电子书")
    scan_parser.add_argument("directory", help="目标目录路径")
    scan_parser.add_argument(
        "--ext",
        default="pdf,epub,mobi,azw3,djvu,cbr,cbz",
        help="支持的扩展名，逗号分隔（默认: pdf,epub,mobi,azw3,djvu,cbr,cbz）"
    )
    scan_parser.add_argument("--output", "-o", help="输出到 JSON 文件（可选）")
    scan_parser.add_argument("--incremental", action="store_true", help="增量模式：仅返回上次扫描后新增/变更的文件")

    # clean-titles
    clean_parser = subparsers.add_parser("clean-titles", help="从扫描结果中清洗书名")
    clean_parser.add_argument("scan_file", help="scan 输出的 JSON 文件路径")
    clean_parser.add_argument("--output", "-o", help="输出到 JSON 文件（可选）")

    # clean-source
    cs_parser = subparsers.add_parser("clean-source", help="清理 --copy 模式产生的 .source 标记文件")
    cs_parser.add_argument("directory", help="要清理的目录路径")
    cs_parser.add_argument("--dry-run", action="store_true", help="仅预览，不实际删除")

    # move
    move_parser = subparsers.add_parser("move", help="按分类计划移动文件")
    move_parser.add_argument("plan_file", help="分类计划 JSON 文件路径")
    move_parser.add_argument("--dry-run", action="store_true", help="仅预览，不实际移动")
    move_parser.add_argument("--copy", action="store_true", help="复制模式：先复制，源文件标记为 .source")

    # report
    report_parser = subparsers.add_parser("report", help="生成整理报告")
    report_parser.add_argument("directory", help="目标目录路径")
    report_parser.add_argument("--output", "-o", help="输出到 JSON 文件（可选）")

    # index
    index_parser = subparsers.add_parser("index", help="生成 Markdown 格式的图书索引目录")
    index_parser.add_argument("directory", help="已整理的图书根目录路径")
    index_parser.add_argument("--output", "-o", default="图书索引.md", help="输出 Markdown 文件路径（默认: 图书索引.md）")

    # undo
    undo_parser = subparsers.add_parser("undo", help="撤销上一次整理，恢复文件到原始位置")
    undo_parser.add_argument("manifest_file", nargs="?", help=".move_manifest.json 路径（默认自动查找）")
    undo_parser.add_argument("--dry-run", action="store_true", help="仅预览撤销操作，不实际执行")

    args = parser.parse_args()

    if args.command == "scan":
        extensions = {f".{e.strip().lower()}" for e in args.ext.split(",") if e.strip()}
        if args.incremental:
            scan_result = scan_incremental(args.directory, extensions)
            files = scan_result["files"]
            result = {
                "command": "scan",
                "directory": args.directory,
                "extensions": sorted(extensions),
                "incremental": scan_result["incremental"],
                "file_count": len(files),
                "files": files,
            }
        else:
            files = scan_directory(args.directory, extensions)
            result = {
                "command": "scan",
                "directory": args.directory,
                "extensions": sorted(extensions),
                "file_count": len(files),
                "files": files,
            }
        output = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print("扫描结果已保存到: " + args.output)
        else:
            print(output)

    elif args.command == "clean-titles":
        data = clean_titles(args.scan_file)
        output = json.dumps(data, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print("清洗结果已保存到: " + args.output)
        else:
            print(output)

    elif args.command == "clean-source":
        result = clean_source_files(args.directory, dry_run=args.dry_run)
        output = json.dumps(result, ensure_ascii=False, indent=2)
        print(output)

    elif args.command == "move":
        stats = move_files(args.plan_file, dry_run=args.dry_run, copy_mode=args.copy)
        output = json.dumps(stats, ensure_ascii=False, indent=2)
        print(output)

    elif args.command == "report":
        report = generate_report(args.directory)
        output = json.dumps(report, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print("报告已保存到: " + args.output)
        else:
            print(output)

    elif args.command == "index":
        md = generate_index(args.directory)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md)
        print("索引已保存到: " + args.output)

    elif args.command == "undo":
        result = undo_move(args.manifest_file, dry_run=args.dry_run)
        output = json.dumps(result, ensure_ascii=False, indent=2)
        print(output)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

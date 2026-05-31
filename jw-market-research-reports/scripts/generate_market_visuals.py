#!/usr/bin/env python3
"""
市场研究报告可视化生成器

批量生成市场研究报告所需的可视化图表，
使用 scientific-schematics 和 generate-image 技能。

默认行为：仅生成 5-6 个核心可视化
使用 --all 标志生成全部 28 个扩展可视化

用法：
    # 生成核心 5-6 个可视化（推荐用于报告起步）
    python generate_market_visuals.py --topic "电动汽车充电" --output-dir figures/

    # 生成全部 27 个可视化（全面覆盖）
    python generate_market_visuals.py --topic "AI医疗" --output-dir figures/ --all

    # 跳过已存在的文件
    python generate_market_visuals.py --topic "主题" --output-dir figures/ --skip-existing
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


# 可视化定义及提示词
# 每个元组：(文件名, 工具, 提示词模板, 是否核心)
# is_core=True 表示优先生成的 5-6 个核心可视化

CORE_VISUALS = [
    # 优先级 1：市场增长趋势图
    (
        "01_market_growth_trajectory.png",
        "scientific-schematics",
        "柱状图 {topic} 市场增长 2020 至 2034。历史柱形 2020-2024 深蓝色，"
        "预测柱形 2025-2034 浅蓝色。Y轴为十亿美元，X轴为年份。"
        "标注复合年均增长率。每个柱形带数据标签。2024与2025之间竖虚线分隔。"
        "标题：市场增长趋势。专业白色背景"
    ),

    # 优先级 2：TAM/SAM/SOM
    (
        "02_tam_sam_som.png",
        "scientific-schematics",
        "{topic} 市场 TAM SAM SOM 同心圆图。外圈 TAM 全部可及市场。"
        "中圈 SAM 可服务可及市场。内圈 SOM 可获得可服务市场。"
        "每个标注缩写和全称。"
        "蓝色渐变外深内浅。白色背景专业外观"
    ),

    # 优先级 3：波特五力分析
    (
        "03_porters_five_forces.png",
        "scientific-schematics",
        "{topic} 波特五力分析图。中心框为同业竞争及评级。"
        "四周框通过箭头连接至中心：顶部新进入者威胁，"
        "左侧供应商议价能力，右侧买方议价能力，"
        "底部替代品威胁。颜色编码 高=红，中=黄，低=绿。"
        "每个框包含 2-3 个关键因素。专业外观"
    ),

    # 优先级 4：竞争定位矩阵
    (
        "04_competitive_positioning.png",
        "scientific-schematics",
        "{topic} 2x2 竞争定位矩阵。X轴市场聚焦 利基到广泛。"
        "Y轴解决方案 产品到平台。象限：右上平台领导者，"
        "左上利基平台，右下产品领导者，左下专精者。"
        "绘制 8-10 个企业圆圈并标注名称。圆圈大小等于市场份额。"
        "附图例说明尺寸。专业外观"
    ),

    # 优先级 5：风险热力图
    (
        "05_risk_heatmap.png",
        "scientific-schematics",
        "{topic} 风险热力图矩阵。X轴影响 低 中 高 严重。"
        "Y轴概率 不太可能 可能 较可能 非常可能。"
        "单元格颜色：绿色低风险，黄色中等，橙色高风险，红色严重。"
        "绘制 10-12 个编号风险 R1 R2 等作为标注点。"
        "附风险名称图例。专业清晰"
    ),

    # 优先级 6：执行摘要信息图（可选）
    (
        "06_exec_summary_infographic.png",
        "generate-image",
        "{topic} 市场研究执行摘要信息图，单页布局，"
        "中央大指标显示市场规模，四个象限显示增长率、"
        "主要参与者、头部细分领域、区域领导者，现代扁平化设计，"
        "专业蓝绿配色方案，简洁白色背景，商务美学"
    ),
]

EXTENDED_VISUALS = [
    # 产业生态图
    (
        "07_industry_ecosystem.png",
        "scientific-schematics",
        "{topic} 市场产业生态价值链图。水平从左到右流动："
        "供应商框 → 制造商框 → 分销商框 → 终端用户框。"
        "每个主框下方展示 3-4 个小框标注典型参与者类型。实线箭头为产品流，"
        "虚线箭头为资金流。上方为监管监督层。"
        "专业蓝色配色方案，白色背景，标签清晰"
    ),

    # 区域分布
    (
        "08_regional_breakdown.png",
        "scientific-schematics",
        "{topic} 区域市场分布饼图。北美 40% 深蓝，"
        "欧洲 28% 中蓝，亚太 22% 蓝绿，拉丁美洲 6% 浅蓝，"
        "中东非洲 4% 灰蓝。每块显示百分比。右侧图例。"
        "标题：按区域划分的市场规模。专业外观"
    ),

    # 细分领域增长
    (
        "09_segment_growth.png",
        "scientific-schematics",
        "{topic} 细分领域增长对比横向柱状图。Y轴 5-6 个细分领域名称，"
        "X轴 CAGR 百分比 0-30%。柱形颜色从绿（最高）到蓝（最低）。"
        "数据标签含百分比。按从高到低排序。"
        "标题：细分领域增长率对比。含市场平均线"
    ),

    # 驱动因素影响矩阵
    (
        "10_driver_impact_matrix.png",
        "scientific-schematics",
        "{topic} 2x2 驱动因素影响评估矩阵。X轴影响 低到高，"
        "Y轴概率 低到高。象限：右上关键驱动因素红色，"
        "左上关注监控黄色，右下密切关注黄色，"
        "左下次要优先绿色。绘制 8 个标注驱动因素圆点。"
        "圆点大小表示当前影响。专业清晰标签"
    ),

    # PESTLE 分析
    (
        "11_pestle_analysis.png",
        "scientific-schematics",
        "{topic} 市场 PESTLE 六边形分析图。中心六边形标注市场分析。"
        "六个外围六边形：政治红色，经济蓝色，社会绿色，"
        "技术橙色，法律紫色，环境蓝绿。每个外围六边形"
        "包含 2-3 个关键因素要点。连线连接中心与各外围。"
        "专业外观文字清晰可读"
    ),

    # 趋势时间线
    (
        "12_trends_timeline.png",
        "scientific-schematics",
        "{topic} 2024 至 2030 水平趋势时间线。在不同年份绘制 6-8 个新兴趋势。"
        "每个趋势含图标、名称、简要描述。颜色编码："
        "技术趋势蓝色，市场趋势绿色，监管趋势橙色。"
        "2024 处标注当前位置。专业清晰标签"
    ),

    # 市场份额图
    (
        "13_market_share.png",
        "scientific-schematics",
        "{topic} 市场份额饼图 前 10 家企业。企业A 18% 深蓝，"
        "企业B 15% 中蓝，企业C 12% 蓝绿，企业D 10% 浅蓝，"
        "另外 5 家企业各 5-8% 不同蓝色，其他 15% 灰色。"
        "扇区上标注百分比。图例含企业名称。"
        "标题：企业市场份额。色盲友好配色专业"
    ),

    # 战略群组图
    (
        "14_strategic_groups.png",
        "scientific-schematics",
        "{topic} 战略群组图。X轴地理范围 区域到全球。"
        "Y轴产品广度 窄到宽。绘制 4-5 个椭圆气泡代表战略群组。"
        "每个气泡含 2-4 个企业名称。气泡大小等于集体市场份额。"
        "标注群组：全球综合型、区域专精型、聚焦创新型。"
        "不同群组不同颜色。专业清晰标签"
    ),

    # 客户细分
    (
        "15_customer_segments.png",
        "scientific-schematics",
        "{topic} 客户细分树状图。大型企业 45% 深蓝，"
        "中型企业 30% 中蓝，小型企业 18% 浅蓝，消费者 7% 蓝绿。"
        "每个细分显示名称和百分比。标题：按市场份额的客户细分。"
        "专业外观标签清晰"
    ),
    (
        "16_segment_attractiveness.png",
        "scientific-schematics",
        "{topic} 2x2 细分吸引力矩阵。X轴细分规模 小到大。"
        "Y轴增长率 低到高。象限：右上优先重点投资绿色，"
        "左上投资增长黄色，右下收获橙色，"
        "左下降低优先灰色。绘制客户细分为圆圈。"
        "圆圈大小等于盈利能力。不同颜色。专业"
    ),
    (
        "17_customer_journey.png",
        "scientific-schematics",
        "{topic} 客户旅程水平流程图。5 个阶段从左到右：认知、"
        "考虑、决策、实施、拥护。每个阶段下方三行显示：关键活动、"
        "痛点、触点。每个阶段配图标。"
        "颜色渐变从浅到深。专业清晰标签"
    ),

    # 技术路线图
    (
        "18_technology_roadmap.png",
        "scientific-schematics",
        "{topic} 2024 至 2030 技术路线图。三条平行水平轨道："
        "核心技术蓝色，新兴技术绿色，使能技术橙色。"
        "各轨道上标注里程碑和技术引入节点。垂直连线连接"
        "相关技术。年份标记。标注技术名称。专业外观"
    ),
    (
        "19_innovation_curve.png",
        "scientific-schematics",
        "{topic} 技术成熟度曲线（Gartner 炒作周期）。五个阶段："
        "创新萌芽上升，过高期望峰值在顶部，幻灭低谷在底部，"
        "稳步爬升复苏上升，生产成熟期平稳。"
        "在曲线上绘制 6-8 个技术并标注名称。按类别着色。专业清晰标签"
    ),

    # 监管时间线
    (
        "20_regulatory_timeline.png",
        "scientific-schematics",
        "{topic} 2020 至 2028 监管时间线。过去法规深蓝实心标记，"
        "当前法规绿色标记，即将出台法规浅蓝虚线。每个标注法规名称、日期、"
        "简要描述。2024 处垂直标注「当前」线。专业外观标签清晰"
    ),

    # 风险应对矩阵
    (
        "21_risk_mitigation.png",
        "scientific-schematics",
        "{topic} 风险应对图。左列为橙红色风险框。"
        "右列为绿蓝色应对策略框。箭头连接"
        "风险与应对措施。按类别分组。风险严重程度用颜色深浅表示。"
        "包含预防和响应措施。专业清晰标签"
    ),

    # 机会矩阵
    (
        "22_opportunity_matrix.png",
        "scientific-schematics",
        "{topic} 2x2 机会矩阵。X轴市场吸引力 低到高。"
        "Y轴胜出能力 低到高。象限：右上积极进取绿色，"
        "左上能力建设黄色，右下选择性投资黄色，"
        "左下回避退出红色。绘制 6-8 个机会圆点并标注。"
        "大小等于机会价值。专业"
    ),

    # 建议优先级矩阵
    (
        "23_recommendation_priority.png",
        "scientific-schematics",
        "{topic} 建议优先级 2x2 矩阵。X轴投入 低到高。"
        "Y轴影响 低到高。象限：左上速赢项绿色优先执行，"
        "右上重大项目蓝色谨慎规划，左下填充项灰色有空再做，"
        "右下吃力不讨好红色避免。绘制 6-8 个编号建议。专业"
    ),

    # 实施时间线
    (
        "24_implementation_timeline.png",
        "scientific-schematics",
        "{topic} 24 个月实施甘特图。阶段1基础建设 第1-6月 深蓝。"
        "阶段2构建开发 第4-12月 中蓝。阶段3规模扩展 第10-18月 蓝绿。"
        "阶段4优化完善 第16-24月 浅蓝。各阶段重叠。"
        "关键里程碑用菱形标记。X轴月份刻度。专业"
    ),

    # 里程碑追踪
    (
        "25_milestone_tracker.png",
        "scientific-schematics",
        "{topic} 水平时间线里程碑追踪 8-10 个里程碑。"
        "每个显示日期、名称、状态：已完成绿色勾选，进行中黄色圆圈，"
        "待开始灰色圆圈。按阶段分组。阶段标签在上方。"
        "连线贯穿时间线。专业"
    ),

    # 财务预测
    (
        "26_financial_projections.png",
        "scientific-schematics",
        "{topic} 5 年预测组合柱状图和折线图。柱状图为收入"
        "主Y轴美元。折线图为增长率次Y轴百分比。"
        "三种情景：保守灰色，基准蓝色，乐观绿色。"
        "X轴第1-5年。数据标签。图例。标题5年财务预测。专业"
    ),

    # 情景分析
    (
        "27_scenario_analysis.png",
        "scientific-schematics",
        "{topic} 情景对比分组柱状图。X轴指标：第5年收入、"
        "第5年EBITDA、市场份额、ROI。每指标三根柱：保守灰色，"
        "基准蓝色，乐观绿色。数据标签。图例。"
        "标题情景分析对比。专业清晰标签"
    ),
]


def get_script_path(tool: str) -> Path:
    """获取对应生成工具的脚本路径。"""
    base_path = Path(__file__).parent.parent.parent  # skills 目录

    if tool == "scientific-schematics":
        return base_path / "scientific-schematics" / "scripts" / "generate_schematic.py"
    elif tool == "generate-image":
        return base_path / "generate-image" / "scripts" / "generate_image.py"
    else:
        raise ValueError(f"未知工具: {tool}")


def generate_visual(
    filename: str,
    tool: str,
    prompt: str,
    output_dir: Path,
    topic: str,
    skip_existing: bool = False,
    verbose: bool = False
) -> bool:
    """使用对应工具生成单个可视化。"""
    output_path = output_dir / filename

    # 如果已存在且设置了跳过
    if skip_existing and output_path.exists():
        if verbose:
            print(f"  [跳过] {filename} 已存在")
        return True

    # 用主题格式化提示词
    formatted_prompt = prompt.format(topic=topic)

    # 获取脚本路径
    script_path = get_script_path(tool)

    if not script_path.exists():
        print(f"  [错误] 脚本未找到: {script_path}")
        return False

    # 构建命令
    if tool == "scientific-schematics":
        cmd = [
            sys.executable,
            str(script_path),
            formatted_prompt,
            "-o", str(output_path),
            "--doc-type", "report"
        ]
    else:  # generate-image
        cmd = [
            sys.executable,
            str(script_path),
            formatted_prompt,
            "--output", str(output_path)
        ]

    if verbose:
        print(f"  [生成] {filename}")
        print(f"        工具: {tool}")
        print(f"        提示词: {formatted_prompt[:80]}...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 每张图 2 分钟超时
        )

        if result.returncode == 0:
            if verbose:
                print(f"  [完成] {filename} 生成成功")
            return True
        else:
            print(f"  [错误] {filename} 失败:")
            if result.stderr:
                print(f"         {result.stderr[:200]}")
            return False

    except subprocess.TimeoutExpired:
        print(f"  [超时] {filename} 生成超时")
        return False
    except Exception as e:
        print(f"  [错误] {filename}: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="生成市场研究报告可视化（默认：仅 5-6 个核心可视化）"
    )
    parser.add_argument(
        "--topic", "-t",
        required=True,
        help="市场主题（如 '电动汽车充电基础设施'）"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="figures",
        help="生成图片的输出目录（默认：figures）"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="生成全部 27 个扩展可视化（默认：仅核心 5-6 个）"
    )
    parser.add_argument(
        "--skip-existing", "-s",
        action="store_true",
        help="文件已存在时跳过生成"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细输出"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅显示将要生成的内容，不实际执行"
    )
    parser.add_argument(
        "--only",
        type=str,
        help="仅生成匹配此模式的可视化（如 '01_'、'porter'）"
    )

    args = parser.parse_args()

    # 创建输出目录
    output_dir = Path(args.output_dir)
    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"市场研究可视化生成器")
    print(f"{'='*60}")
    print(f"主题: {args.topic}")
    print(f"输出目录: {output_dir.absolute()}")
    print(f"模式: {'全部可视化（27个）' if args.all else '仅核心可视化（5-6个）'}")
    print(f"跳过已有: {args.skip_existing}")
    print(f"{'='*60}\n")

    # 根据 --all 标志选择可视化集合
    if args.all:
        visuals_to_generate = CORE_VISUALS + EXTENDED_VISUALS
        print("生成全部可视化（核心 + 扩展）\n")
    else:
        visuals_to_generate = CORE_VISUALS
        print("仅生成核心可视化（使用 --all 生成扩展集）\n")

    # 如果指定了 --only 则过滤
    if args.only:
        pattern = args.only.lower()
        visuals_to_generate = [
            v for v in visuals_to_generate
            if pattern in v[0].lower() or pattern in v[2].lower()
        ]
        print(f"已过滤为 {len(visuals_to_generate)} 个匹配 '{args.only}' 的可视化\n")

    if args.dry_run:
        print("预演模式 - 以下可视化将被生成：\n")
        for filename, tool, prompt in visuals_to_generate:
            formatted = prompt.format(topic=args.topic)
            print(f"  {filename}")
            print(f"    工具: {tool}")
            print(f"    提示词: {formatted[:60]}...")
            print()
        return

    # 生成全部可视化
    total = len(visuals_to_generate)
    success = 0
    failed = 0
    skipped = 0

    for i, (filename, tool, prompt) in enumerate(visuals_to_generate, 1):
        print(f"\n[{i}/{total}] 正在生成 {filename}...")

        result = generate_visual(
            filename=filename,
            tool=tool,
            prompt=prompt,
            output_dir=output_dir,
            topic=args.topic,
            skip_existing=args.skip_existing,
            verbose=args.verbose
        )

        if result:
            if args.skip_existing and (output_dir / filename).exists():
                skipped += 1
            else:
                success += 1
        else:
            failed += 1

    # 打印汇总
    print(f"\n{'='*60}")
    print(f"生成完成")
    print(f"{'='*60}")
    print(f"总计:    {total}")
    print(f"成功:    {success}")
    print(f"跳过:    {skipped}")
    print(f"失败:    {failed}")
    print(f"{'='*60}")

    if failed > 0:
        print(f"\n警告: {failed} 个可视化生成失败。")
        print("请查看上方输出了解错误详情。")
        print("失败的可视化可能需要手动生成。")

    print(f"\n输出目录: {output_dir.absolute()}")


if __name__ == "__main__":
    main()

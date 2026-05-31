#!/usr/bin/env python3
"""
Stage 2 extraction for 《中国国家治理的制度逻辑：一个组织学研究》
周雪光组织学著作 - 学术类书籍
"""
import os
import re
import json

BOOK_DIR = "/root/books/中国国家治理的制度逻辑：一个组织学研究 - 周雪光"
CANDIDATES_DIR = os.path.join(BOOK_DIR, "candidates")
os.makedirs(CANDIDATES_DIR, exist_ok=True)

# Load book index
with open(os.path.join(BOOK_DIR, "book-index.json")) as f:
    book_index = json.load(f)

meaningful_chapters = {c["id"]: c for c in book_index["chapters"] if c["is_meaningful"]}

# Read all meaningful chapters
chapters = {}
for cid in sorted(meaningful_chapters.keys()):
    ch_path = os.path.join(BOOK_DIR, "chapters", f"{cid}.txt")
    if os.path.exists(ch_path):
        with open(ch_path, encoding="utf-8") as f:
            chapters[cid] = f.read()

print(f"Loaded {len(chapters)} chapters")

# Read definitions snippets
with open(os.path.join(BOOK_DIR, "snippets", "definitions.json"), encoding="utf-8") as f:
    definitions = json.load(f)

print(f"Loaded {len(definitions)} definition snippets")

# Read quotes
with open(os.path.join(BOOK_DIR, "snippets", "quotes.json"), encoding="utf-8") as f:
    quotes = json.load(f)

print(f"Loaded {len(quotes)} quote snippets")

# Read cases
with open(os.path.join(BOOK_DIR, "snippets", "cases.json"), encoding="utf-8") as f:
    cases_snippets = json.load(f)

print(f"Loaded {len(cases_snippets)} case snippets")

# ============================================================
# FRAMEWORKS
# ============================================================
frameworks = []

# Framework 1: Control Rights Theory (控制权理论)
frameworks.append({
    "id": "f01",
    "title": "控制权理论",
    "type": "framework",
    "source_chapter": "ch006 / 第3章 政府的治理模式",
    "source_line": 1,
    "source_quote": "中央政府拥有行政统辖、规划的权力，特别体现在人事安排和资源调配的权力上。而上下级政府间的'控制权'分配——哪些权力集中于上级，哪些权力下放给下级——决定了政府内部的治理模式。",
    "summary": "周雪光提出的核心分析框架：政府内部的\"控制权\"不是单一维度的集权或分权，而是在不同层次间分割的不同权力束。上级保留人事任免权、考核权、资源分配权，下级拥有执行权辖区内的具体事务处置权。这种\"控制权\"的分割方式塑造了上下级间的独特关系——不是纯粹的命令-执行关系，而是包含谈判、共谋、变通的互动关系。",
    "keywords": ["控制权", "委托代理", "政府治理", "上下级关系"],
    "v3_pass": True,
    "v3_reason": "这是作者原创的核心概念，突破了传统集权-分权的二元框架，提出'控制权'作为分析政府内部关系的核心变量。",
    "v2_scenario": "理解中央巡视组下派时地方政府的应对行为：哪些事项地方有自主空间，哪些必须严格按中央口径回应。",
    "related": ["f02", "f03"]
})

# Framework 2: 运动型治理机制
frameworks.append({
    "id": "f02",
    "title": "运动型治理机制",
    "type": "framework",
    "source_chapter": "ch007 / 第4章 运动型治理机制",
    "source_line": 1,
    "source_quote": "运动型治理机制指的是，通过政治动员而非常规行政程序来推动中心工作完成的治理方式。它是中央政府绕过常规官僚层级、直接穿透到基层的治理手段。",
    "summary": "中国政治运行中独特的治理模式：常规官僚体制按程序、按规章运作，但当中心任务需要突破日常行政节奏时，运动型治理通过政治动员、压力传导、跨层级调动来强行推进。其特点是打破部门边界、暂时搁置常规程序、以政治目标替代专业目标。运动型治理结束后，常规体制恢复。",
    "keywords": ["运动型治理", "政治动员", "常规行政", "压力型体制"],
    "v3_pass": True,
    "v3_reason": "这是作者对当代中国政治运行模式的核心概括，揭示了中国政府'条块关系'中独特的运动式推进机制。",
    "v2_scenario": "当某项政策被列为'政治任务'时，常规的项目审批流程被搁置，多个部门被临时抽调人员组成联合工作组。",
    "related": ["f01", "f03"]
})

# Framework 3: 逆向软预算约束
frameworks.append({
    "id": "f03",
    "title": "逆向软预算约束",
    "type": "framework",
    "source_chapter": "ch012 / 第9章 逆向软预算约束",
    "source_line": 1,
    "source_quote": "软预算约束原指下级组织的预算约束软化，依赖上级财政救助。逆向软预算约束则表现为：基层组织在完成预算后，向上级争取追加预算——通过项目包装、问题化策略将本地区的问题向上传递，获取更多资源。",
    "summary": "与经典软预算约束（组织向上级要钱）方向相反，逆向软预算约束指基层政府在正常预算之外主动制造问题、放大问题严重性，以此换取上级追加资源。这一机制解释了基层政府的'讨价还价'行为和基层债务累积的制度根源。",
    "keywords": ["软预算约束", "基层债务", "政府间谈判", "资源向上争取"],
    "v3_pass": True,
    "v3_reason": "对科尔奈经典概念的创造性反转，揭示了中国地方政府独特的财政行为逻辑。",
    "v2_scenario": "某贫困县每年都向上级汇报本地自然灾害频发、基础设施落后，以争取更多转移支付和专项资金。",
    "related": ["f01", "f07"]
})

# Framework 4: 一统体制与有效治理的矛盾
frameworks.append({
    "id": "f04",
    "title": "一统体制与有效治理的基本矛盾",
    "type": "framework",
    "source_chapter": "ch004 / 第1章 导论",
    "source_line": 1,
    "source_quote": "中国国家治理的一个深刻矛盾是一统体制与有效治理之间的矛盾，集中表现在中央管辖权与地方治理权间的紧张和不兼容：前者趋于权力、资源向上集中，从而削弱了地方政府解决实际问题的能力；而后者又常常表现为各行其是、偏离失控，对一统体制的中央核心产生威胁。",
    "summary": "这是贯穿全书的核心矛盾框架：中央政府面临两难选择——加强中央集权可以维护统一性，但会削弱地方有效治理能力；放权给地方可以提升治理有效性，但可能导致地方失控、威胁中央权威。这一矛盾无法根本解决，只能在动态中寻找暂时平衡。",
    "keywords": ["一统体制", "有效治理", "中央地方关系", "集权分权"],
    "v3_pass": True,
    "v3_reason": "全书核心命题，所有其他制度机制都围绕这一基本矛盾展开。",
    "v2_scenario": "理解中央为何在'集权-放权'之间反复摇摆：每一轮集权后地方活力下降触发放权，放权后地方失控又触发新一轮集权。",
    "related": ["f01", "f02", "f05"]
})

# Framework 5: 逐级代理制度
frameworks.append({
    "id": "f05",
    "title": "逐级代理制与执行灵活性",
    "type": "framework",
    "source_chapter": "ch004 / 第1章 导论",
    "source_line": 1,
    "source_quote": "决策一统性与执行灵活性以及逐级代理制的动态平衡，是维系一统体制的重要机制。中央政府制定统一政策，但将执行权逐级下放，默许下级在执行中的灵活变通。",
    "summary": "逐级代理制是指中央政府将政策执行任务层层委托给下级政府，同时允许下级在执行方式上有所变通。这一制度设计缓解了一统体制与有效治理的矛盾：中央保持决策权统一，地方保有执行弹性。但这也导致了'共谋现象'和'拼凑应对'等非正式行为。",
    "keywords": ["逐级代理", "执行灵活性", "变通", "共谋"],
    "v3_pass": True,
    "v3_reason": "解释了为何中国官僚体制在实际运行中呈现出'松散联合'的特征。",
    "v2_scenario": "中央下达节能减排指标，省级政府分解到各市时允许一定弹性幅度，市级在具体企业执行时又进一步调整。",
    "related": ["f01", "f06"]
})

# Framework 6: 拼凑应对策略
frameworks.append({
    "id": "f06",
    "title": "拼凑应对：多重逻辑下的基层政府行为",
    "type": "framework",
    "source_chapter": "ch010 / 第7章 \"拼凑应对\"",
    "source_line": 1,
    "source_quote": "基层政府在多重制度逻辑——官僚制逻辑、政策执行逻辑、地方利益逻辑——之间进行'拼凑应对'：不是按某一逻辑严格行事，而是在多种逻辑之间寻找可行的操作空间。",
    "summary": "基层政府面对相互冲突的制度要求时，不是线性地选择某一方，而是在多重逻辑之间'拼凑'出可行的解决方案。这种行为模式解释了基层政府为何常常'看似矛盾'的行为——实际上是对多重压力的务实回应。",
    "keywords": ["拼凑应对", "基层政府行为", "多重逻辑", "变通策略"],
    "v3_pass": True,
    "v3_reason": "从组织学角度解释了基层政府的非正式行为，突破了'执行不力'的简单道德判断。",
    "v2_scenario": "某乡镇在迎接上级环保检查时，暂时关闭本地污染企业，但检查结束后立即恢复生产——这是对中央环保要求与地方就业压力之间矛盾的拼凑应对。",
    "related": ["f02", "f05", "f07"]
})

# Framework 7: 官僚制的韦伯理想类型
frameworks.append({
    "id": "f07",
    "title": "韦伯官僚制理想类型与中国现实",
    "type": "framework",
    "source_chapter": "ch005 / 第2章 国家治理逻辑与中国官僚制",
    "source_line": 1,
    "source_quote": "官僚组织的基本特点表现在权力关系明确、等级层次有序的组织结构，通过专业化人员和正式规章制度来贯彻落实自上而下的政策指令。中国官僚制具有韦伯所描述的合理性特征，但又在权力向上集中程度、非正式关系的作用等方面表现出独特的偏离。",
    "summary": "以韦伯的官僚制理想类型为参照系，分析中国官僚制的独特性：中国官僚制具备形式合理性（等级结构、规章制度、专业化），但在干部管理制度（党管干部）、上下级关系（非正式互动）、预算约束（软约束）等方面偏离了韦伯模型，形成了一种'形式合理、实质独特'的官僚制形态。",
    "keywords": ["韦伯官僚制", "形式合理性", "党管干部", "中国官僚制"],
    "v3_pass": True,
    "v3_reason": "将中国官僚制置入比较组织学的分析框架，揭示其与传统韦伯模型的异同。",
    "v2_scenario": "比较中国地方政府与西方国家地方政府的决策程序：两者都有等级结构，但中国地方政府的决策灵活性远大于西方。",
    "related": ["f01", "f04"]
})

# Framework 8: 共谋现象
frameworks.append({
    "id": "f08",
    "title": "基层政府间的共谋现象",
    "type": "framework",
    "source_chapter": "ch010 / 第7章 基层政府间的\"共谋现象\"",
    "source_line": 1,
    "source_quote": "共谋现象指的是同一层级的基层政府（如县级政府之间、乡镇政府之间）在应对上级检查和中央政策时形成的非正式合作：事先通气、统一口径、共同应对。",
    "summary": "共谋是基层政府在逐级代理制度下形成的非正式合作机制。当上级检查来临时，同级地方政府会协调行动，统一应对策略，共享信息，甚至联合包装项目。这种非正式合作虽然降低了被问责的风险，但也削弱了中央政策的实际效果。",
    "keywords": ["共谋", "基层政府", "非正式合作", "应付检查"],
    "v3_pass": True,
    "v3_reason": "揭示了基层政府在压力型体制下的组织行为创新，是理解中国基层治理的关键概念。",
    "v2_scenario": "相邻的几个乡镇在迎接上级扶贫检查前，统一口径、共享材料，甚至互相派人支援。",
    "related": ["f05", "f06"]
})

# Framework 9: 组织成本与治理规模
frameworks.append({
    "id": "f09",
    "title": "治理规模与组织成本",
    "type": "framework",
    "source_chapter": "ch004 / 第1章 导论",
    "source_line": 1,
    "source_quote": "国家治理规模所面临的负荷和挑战是所谓'技术治理手段'所无法解决的。治理规模越大，组织成本越高，信息不对称问题越严重，有效治理越困难。",
    "summary": "将治理规模作为核心变量引入国家分析：中国治理规模（近14亿人口、960万平方公里、多元文化）产生了巨大的组织成本，包括信息传递成本、协调成本、激励扭曲成本等。技术手段（数目字管理）可以缓解但不能根本解决这一困境。",
    "keywords": ["治理规模", "组织成本", "信息不对称", "数目字管理"],
    "v3_pass": True,
    "v3_reason": "将组织学理论（组织规模与成本）与国家治理分析结合，解释了为何中国必须依赖特殊的治理机制。",
    "v2_scenario": "理解为何中央政府无法完全掌握地方实际情况：信息从基层向上传递过程中逐级失真，14亿人口的国家元首看到的可能只是层层加工后的信息。",
    "related": ["f04", "f07"]
})

# ============================================================
# PRINCIPLES
# ============================================================
principles = []

# Principle 1: 官僚组织的等级制度是维系一统体制的核心
principles.append({
    "id": "p01",
    "title": "官僚组织的等级制度是维系一统体制的核心",
    "type": "principle",
    "source_chapter": "ch004 / 第1章 导论",
    "source_line": 1,
    "source_quote": "维系一统体制的两个核心组织机制：一是官僚组织制度，二是认同中央权威的观念制度。前者涉及中央政府及其下属各级政府机构间的等级结构。",
    "summary": "中国一统体制的维系依赖两个机制：官僚组织的等级结构（自上而下的人事任免、资源调配权力）和观念制度（共享的政治认同）。其中官僚等级制度更为根本——它通过人事控制实现对各级政府的实质性支配。",
    "keywords": ["官僚组织", "等级制度", "一统体制", "人事管理"],
    "v3_pass": True,
    "v3_reason": "明确了一统体制的两大制度支柱，为理解中国政治提供了基本框架。",
    "v2_scenario": "理解为何中央可以叫停地方重大政策：各级官员的任免权在中央，这使得中央对地方具有实质性控制力。",
    "related": ["f01", "f07"]
})

# Principle 2: 观念制度必须持续维护
principles.append({
    "id": "p02",
    "title": "一统观念制度必须持续通过政治动员来维护",
    "type": "principle",
    "source_chapter": "ch004 / 第1章 导论",
    "source_line": 1,
    "source_quote": "在当代中国，国家依靠马列主义统一执政党内部的观念，曾有效地替代了儒家文化观念制度的维系功能。但这一观念制度需要通过持续不断的政治活动来不断维系、修补和强化。",
    "summary": "与官僚组织制度的刚性不同，观念制度是脆弱的，需要持续维护。当代中国通过党内学习、群众运动、思想教育等形式持续强化一统观念。但现代社会的多元分化对这一观念制度构成持续挑战。",
    "keywords": ["观念制度", "政治动员", "意识形态", "社会整合"],
    "v3_pass": True,
    "v3_reason": "揭示了观念制度维系的高成本性和脆弱性，与中国历史上的教化努力相呼应。",
    "v2_scenario": "理解党内学习教育的持续性：这不是形式主义，而是维系观念制度的必要手段。",
    "related": ["p01", "f02"]
})

# Principle 3: 压力型体制是政策执行的基本模式
principles.append({
    "id": "p03",
    "title": "压力型体制是政策执行的基本模式",
    "type": "principle",
    "source_chapter": "ch006 / 第3章 政府的治理模式",
    "source_line": 1,
    "source_quote": "压力型体制指的是上级政府将任务指标分解下派，层层加码，基层政府必须在限定时间内完成，否则面临问责。计划生育领域最早实践了这种体制。",
    "summary": "中国政策执行的核心模式是'压力型体制'：中央定目标、下级签责任书、层层加码、限时完成、一票否决。这一体制确保了政策的高速推进，但也导致数字造假、形式主义等问题。",
    "keywords": ["压力型体制", "层层加码", "一票否决", "指标考核"],
    "v3_pass": True,
    "v3_reason": "概括了中国政策执行的核心机制，是理解基层行为逻辑的关键。",
    "v2_scenario": "理解基层为何经常'数字造假'：不是道德问题，而是压力型体制下的理性选择。",
    "related": ["f02", "f03", "f05"]
})

# Principle 4: 组织规模导致委托代理问题
principles.append({
    "id": "p04",
    "title": "组织规模导致不可避免的委托代理问题",
    "type": "principle",
    "source_chapter": "ch005 / 第2章 韦伯官僚制视角",
    "source_line": 1,
    "source_quote": "官僚组织在委托代理关系中，中央与地方政府双方利益目标不同、信息不对称，在漫长的行政链条中，只能实行层层节制。",
    "summary": "在任何大型组织中，委托代理问题都不可避免——代理人（地方政府）拥有自身利益，与委托人（中央政府）不完全一致，且掌握更多信息。在中国，这一问题因组织规模庞大、层级众多而尤为严重。",
    "keywords": ["委托代理", "信息不对称", "利益不一致", "激励机制"],
    "v3_pass": True,
    "v3_reason": "将经济学委托代理理论应用于中国政府分析，解释了上下级间张力。",
    "v2_scenario": "理解为何地方官员常常'报喜不报忧'：如实汇报可能意味着自己治理能力不足，影响仕途。",
    "related": ["f01", "f07", "f09"]
})

# Principle 5: 软预算约束激励地方突破财政限制
principles.append({
    "id": "p05",
    "title": "软预算约束激励地方政府突破财政限制",
    "type": "principle",
    "source_chapter": "ch012 / 第9章 逆向软预算约束",
    "source_line": 1,
    "source_quote": "当基层政府的预算约束软化时，它们有动机突破预算限制、向上级争取更多资源，而不是在给定预算内精打细算。",
    "summary": "经典的软预算约束理论指出，下级组织在预算超支时可以指望上级救助，这降低了其控制成本的动力。中国出现的是'逆向'版本：基层政府主动制造问题、放大问题，以换取上级追加资源，导致债务累积。",
    "keywords": ["软预算约束", "地方债务", "资源争取", "财政纪律"],
    "v3_pass": True,
    "v3_reason": "对经典概念的创造性应用，揭示了地方债务危机的制度根源。",
    "v2_scenario": "理解为何地方政府负债累累仍不断上新项目：项目失败可以争取上级救助，新项目成功可以换取政绩。",
    "related": ["f03", "p04"]
})

# Principle 6: 运动型治理不能持续
principles.append({
    "id": "p06",
    "title": "运动型治理不能成为常规治理模式",
    "type": "principle",
    "source_chapter": "ch007 / 第4章 运动型治理机制",
    "source_line": 1,
    "source_quote": "运动型治理虽然在短期内可以突破常规行政的繁文缛节、实现快速动员，但运动结束后常规体制恢复，且运动本身会留下诸多后遗症。",
    "summary": "运动型治理是高成本、不可持续的治理模式：它打乱了正常的工作节奏，消耗大量政治资本，且在运动结束后通常导致政策执行的反弹（松绑）。因此运动型治理只能作为'纠偏'机制偶尔使用。",
    "keywords": ["运动型治理", "非常规治理", "纠偏", "政策反弹"],
    "v3_pass": True,
    "v3_reason": "指出了运动型治理的局限性，为理解中国的'运动式整顿'提供了分析框架。",
    "v2_scenario": "理解为何每次运动式治理结束后，相关领域的违规行为往往会'报复性反弹'。",
    "related": ["f02", "p03"]
})

# Principle 7: 非正式制度填补正式制度空白
principles.append({
    "id": "p07",
    "title": "非正式制度是对正式制度缺陷的理性填补",
    "type": "principle",
    "source_chapter": "ch010 / 第7章 基层政府间共谋",
    "source_line": 1,
    "source_quote": "共谋行为不是个人品质问题，而是组织在特定制度环境下的理性应对。正式制度存在缺陷时，非正式制度应运而生填补空白。",
    "summary": "基层政府的共谋、变通、拼凑等行为不是个别官员的道德问题，而是面对正式制度缺陷时的集体理性选择。只要一统体制与有效治理的矛盾存在，这些非正式行为就会持续存在。",
    "keywords": ["非正式制度", "共谋", "理性行为", "制度缺陷"],
    "v3_pass": True,
    "v3_reason": "将非正式行为从道德判断转向制度分析，提供了理解中国基层治理的新视角。",
    "v2_scenario": "理解地方政府的'关系网'：这是应对条块分割、激励不足的理性策略。",
    "related": ["f06", "f08", "p04"]
})

# ============================================================
# CASES
# ============================================================
cases = []

# Case 1: 计划生育政策的成功与代价
cases.append({
    "id": "c01",
    "title": "计划生育政策的运动式推广",
    "type": "case",
    "source_chapter": "ch004 / 第1章 导论",
    "source_line": 1,
    "source_quote": "计划生育政策的成功得益于三个机制：专门的组织机构、强大的激励（'一票否决'考核）、以及大规模持续的宣传教育。这三个机制需要持续的行政投入维持。",
    "summary": "计划生育政策是展示压力型体制和运动式治理效果的经典案例：中央自上而下建立专门机构、设定刚性指标、实施严厉考核，在数十年内实现了人口出生率的急剧下降。但这一成功需要极高的行政成本，难以在其他领域复制。",
    "keywords": ["计划生育", "一票否决", "运动式治理", "行政成本"],
    "v3_pass": True,
    "v3_reason": "提供了理解压力型体制有效性的最佳案例。",
    "v2_scenario": "当某项政策被纳入'一票否决'考核时，地方政府的重视程度和执行力度会急剧上升。",
    "linked_method_hint": "压力型体制与一票否决机制",
    "related": ["p03", "f02"]
})

# Case 2: 大跃进与文革
cases.append({
    "id": "c02",
    "title": "大跃进和文革：运动型治理的极端后果",
    "type": "case",
    "source_chapter": "ch004 / 第1章 导论",
    "source_line": 1,
    "source_quote": "举国体制一以贯之的做法不仅代价昂贵，难以为继，而且常常诱发重大灾难，如'大跃进'和'文革'。",
    "summary": "大跃进（1958-1962）和文革（1966-1976）是运动型治理的极端案例：中央以政治动员方式推动经济发展（农业放卫星）和思想改造（文化革命），打破了常规官僚程序，但导致了灾难性的后果（饥荒和文化断层）。这两个案例说明了压力型体制超越临界点后的崩溃性后果。",
    "keywords": ["大跃进", "文革", "政策失败", "运动型治理"],
    "v3_pass": True,
    "v3_reason": "揭示了压力型体制超越临界点后的灾难性后果，是理解中国政策风险的必要背景。",
    "v2_scenario": "理解为何当前中央强调'稳中求进'：历史上激进政策的教训表明，运动式推进有失控风险。",
    "linked_method_hint": "运动型治理的局限性与失控风险",
    "related": ["f02", "p06"]
})

# Case 3: 基层共谋应对环保检查
cases.append({
    "id": "c03",
    "title": "基层共谋应对中央环保督察",
    "type": "case",
    "source_chapter": "ch010 / 第7章 共谋现象",
    "source_line": 1,
    "source_quote": "中央环保督察组下派期间，地方基层政府会协调行动：统一口径、共享整改材料、互相通气检查时间，甚至派人相互支援应对检查。",
    "summary": "环保督察是理解当代中国共谋行为的理想场景：中央设立高目标（污染防治攻坚战），地方政府在指标压力下形成横向联盟，通过统一应对策略来降低被问责风险，同时维持表面的政策执行。",
    "keywords": ["环保督察", "共谋", "基层应对", "中央地方关系"],
    "v3_pass": True,
    "v3_reason": "提供了理解当前共谋行为的最贴近案例。",
    "v2_scenario": "中央环保督察组到达前，相邻县市的环保局会通过非正式渠道协调应对策略。",
    "linked_method_hint": "共谋行为与压力型体制的交互作用",
    "related": ["f08", "p07", "f06"]
})

# Case 4: 乡镇债务积累
cases.append({
    "id": "c04",
    "title": "乡镇债务积累：逆向软预算约束的案例",
    "type": "case",
    "source_chapter": "ch012 / 第9章 逆向软预算约束",
    "source_line": 1,
    "source_quote": "乡镇政府通过土地财政、项目融资平台等途径大量负债，在预算已经用尽的情况下继续投资。期望项目成功后偿还债务，若失败则期待上级救助。",
    "summary": "1990年代至2010年代，中国乡镇债务快速累积。根因是逆向软预算约束：基层政府发现负债不仅可以发展本地，还有机会获得上级救助（因为上级政府无法承受基层债务危机引发社会不稳定）。这导致基层政府形成了'以债务换发展'的行为模式。",
    "keywords": ["乡镇债务", "土地财政", "软预算约束", "地方融资平台"],
    "v3_pass": True,
    "v3_reason": "揭示了地方债务危机的制度根源，解释了2008年后四万亿刺激政策导致的债务扩张。",
    "v2_scenario": "理解四万亿刺激计划后地方债务急剧膨胀：中央要求地方配套项目，地方通过融资平台举债配套，形成逆向软预算约束的典型场景。",
    "linked_method_hint": "逆向软预算约束与地方债务膨胀机制",
    "related": ["f03", "p05"]
})

# ============================================================
# BOUNDARIES
# ============================================================
boundaries = []

# Boundary 1: 韦伯模型不适用于中国
boundaries.append({
    "id": "b01",
    "title": "韦伯官僚制模型不能直接套用于中国",
    "type": "boundary",
    "source_chapter": "ch005 / 第2章 韦伯官僚制视角",
    "source_line": 1,
    "source_quote": "中国官僚制具有韦伯所描述的合理性特征，但又在权力向上集中程度、非正式关系的作用等方面表现出独特的偏离。直接将韦伯模型套用于中国会产生误判。",
    "summary": "韦伯官僚制模型的核心假设（等级明确、规则至上、非人格化）在西方语境中成立，但中国官僚制存在三重偏离：党管干部（非纯粹的文官制度）、上下级间大量非正式互动（关系、人情）、软预算约束（规则约束力不足）。分析中国官僚制需要修正韦伯模型。",
    "keywords": ["韦伯官僚制", "适用边界", "中国特殊性", "模型修正"],
    "v3_pass": True,
    "v3_reason": "指出了西方组织学理论应用于中国时的边界条件，对理论适用性有清醒认识。",
    "v2_scenario": "不能简单用'法团主义'（corporatism）分析中国地方政府，因为中国地方政府的自主性来源于非正式关系而非正式制度授权。",
    "related": ["f07", "p07"]
})

# Boundary 2: 运动型治理的效果有时限
boundaries.append({
    "id": "b02",
    "title": "运动型治理的效果只在运动期间有效",
    "type": "boundary",
    "source_chapter": "ch007 / 第4章 运动型治理",
    "source_line": 1,
    "source_quote": "运动式治理的有效性在运动期间最高，运动结束后，被压制的矛盾通常会反弹。这限制了运动型治理作为长期治理手段的可行性。",
    "summary": "运动型治理的有效性有时限——它只能在运动存续期间维持高压状态。一旦运动结束或注意力转移，被暂时压制的矛盾会迅速反弹。因此运动型治理不能作为常规治理模式，只能是间歇性的'纠偏'手段。",
    "keywords": ["运动型治理", "有效期", "政策反弹", "时效边界"],
    "v3_pass": True,
    "v3_reason": "指出了运动型治理的时间边界，对于政策设计有直接启示。",
    "v2_scenario": "理解为何每次'严打'运动结束后，相关犯罪率往往会快速回升。",
    "related": ["f02", "p06"]
})

# Boundary 3: 数目字管理不能根本解决治理规模问题
boundaries.append({
    "id": "b03",
    "title": "数目字管理是辅助手段，不能根本解决治理规模问题",
    "type": "boundary",
    "source_chapter": "ch004 / 第1章 导论",
    "source_line": 1,
    "source_quote": "数目字管理在一定意义上有助于减缓治理规模的压力，但不能根本解决其问题。信息有着模糊性，同一信息有着多重解释的可能，因此技术手段不能自行解决治理中的实质性问题。",
    "summary": "近年来中央推动'数目字管理'（税收联网、量化考核、电子监督），但技术手段有三重局限：1）人控制技术，技术本身无自主性；2）技术提供了新的谈判筹码给下级；3）可能导致繁文缛节、降低灵活性。治理规模的根本问题（信息不对称、利益不一致）无法通过技术解决。",
    "keywords": ["数目字管理", "技术治理", "局限", "治理规模"],
    "v3_pass": True,
    "v3_reason": "清醒指出技术治理的局限性，对迷信'数字化改革'有警示意义。",
    "v2_scenario": "理解为何各地'数字化政务平台'建设后，基层填报数据的工作量可能不减反增。",
    "related": ["f09", "p04"]
})

# ============================================================
# GLOSSARY
# ============================================================
glossary = []

# Glossary entries from definitions.json
weber_terms = [d for d in definitions if any(w in d["term"] for w in ["韦伯", "官僚", "科层", "科层制"])]
control_rights = [d for d in definitions if "控制权" in d["term"]]
governance = [d for d in definitions if any(w in d["term"] for w in ["治理", "一统", "集权", "分权"])]

# Add key terms from the actual chapter content
glossary.append({
    "id": "g01",
    "title": "韦伯官僚制（Weberian Bureaucracy）",
    "type": "glossary",
    "source_chapter": "ch005 / 第2章",
    "source_quote": "官僚组织的基本特点表现在权力关系明确、等级层次有序的组织结构，通过专业化人员和正式规章制度来贯彻落实自上而下的政策指令，提高决策和执行的效率。",
    "summary": "韦伯提出的理想型官僚制特征：等级分层、专业分工、正式规则、非人格化运作。马克斯·韦伯认为这是现代组织的基本形式。但中国官僚制在党管干部、非正式关系作用、软预算约束等方面与韦伯模型存在偏离。",
    "keywords": ["韦伯", "官僚制", "科层制", "正式组织"],
    "v3_pass": True,
    "v3_reason": "全书核心理论参照系，读者需要首先理解这一概念。",
    "v2_scenario": "用韦伯模型分析中国地方政府时，需要考虑'党管干部'这一中国特色因素的调节作用。",
    "related": ["f07", "b01"]
})

glossary.append({
    "id": "g02",
    "title": "控制权（Control Rights）",
    "type": "glossary",
    "source_chapter": "ch006 / 第3章",
    "source_quote": "上下级政府间的'控制权'分配——哪些权力集中于上级，哪些权力下放给下级——决定了政府内部的治理模式。",
    "summary": "周雪光提出的核心分析概念：政府内部的权力不是单一维度的'集权'或'分权'，而是由不同维度的权力束构成。上级可以在人事任免上集中权力，在财政上分权，在执行权上给下级留有灵活空间。控制权的分割方式决定了上下级间的互动模式。",
    "keywords": ["控制权", "上下级关系", "政府治理", "权力分配"],
    "v3_pass": True,
    "v3_reason": "这是周雪光原创的核心概念，是理解全书的关键。",
    "v2_scenario": "分析中央与省级关系时，控制权在人事权上高度集中，但在具体经济管理上省级有相当自主权。",
    "related": ["f01", "p04"]
})

glossary.append({
    "id": "g03",
    "title": "运动型治理机制（Mobilization Governance）",
    "type": "glossary",
    "source_chapter": "ch007 / 第4章",
    "source_quote": "运动型治理机制指的是，通过政治动员而非常规行政程序来推动中心工作完成的治理方式。",
    "summary": "中国政治运行中独特的治理模式。它以政治目标替代专业目标，打破部门边界，暂时搁置常规程序，以压力和动员为手段推进工作。其核心特征是'政治优先'和'打破常规'，是理解中国政治运行的关键概念。",
    "keywords": ["运动型治理", "政治动员", "非常规治理", "压力型体制"],
    "v3_pass": True,
    "v3_reason": "概括了中国政治运行的核心特征，是理解中国治理模式的钥匙概念。",
    "v2_scenario": "当某项工作被从'业务工作'提升为'政治任务'时，运动型治理机制启动，执行力度急剧上升。",
    "related": ["f02", "p06", "b02"]
})

glossary.append({
    "id": "g04",
    "title": "软预算约束（Soft Budget Constraint）",
    "type": "glossary",
    "source_chapter": "ch012 / 第9章",
    "source_quote": "软预算约束原指下级组织的预算约束软化，依赖上级财政救助。科尔奈用这一概念解释社会主义国家中国营企业的行为模式。",
    "summary": "科尔奈（ Kornai ）提出的经典概念：社会主义国家中，企业在预算超支时可以指望国家财政救助，因此缺乏控制成本的动力。周雪光在此基础上提出'逆向软预算约束'：基层组织不是等上级来救，而是主动制造问题以换取上级追加资源。",
    "keywords": ["软预算约束", "科尔奈", "逆向", "预算纪律"],
    "v3_pass": True,
    "v3_reason": "对经典概念的创造性发展，解释了地方债务的制度根源。",
    "v2_scenario": "理解为何地方融资平台负债累累仍能持续运转：因为上级政府不会让它们真正破产。",
    "related": ["f03", "p05"]
})

glossary.append({
    "id": "g05",
    "title": "共谋现象（Collusive Behavior）",
    "type": "glossary",
    "source_chapter": "ch010 / 第7章",
    "source_quote": "共谋现象指的是同一层级的基层政府（如县级政府之间、乡镇政府之间）在应对上级检查和中央政策时形成的非正式合作。",
    "summary": "基层政府在压力型体制下形成的横向非正式联盟。当面临上级检查或需要争取资源时，同级地方政府会协调立场、统一口径、共享信息，以降低被问责风险或增加谈判筹码。共谋是中国基层治理中普遍存在的组织行为。",
    "keywords": ["共谋", "横向联盟", "非正式合作", "基层政府"],
    "v3_pass": True,
    "v3_reason": "概括了中国基层政府间关系的核心特征，是理解中国基层政治的重要概念。",
    "v2_scenario": "当中央环保督察组到达某省时，相邻省份的环保局通常会通过非正式渠道通气，统一应对策略。",
    "related": ["f08", "p07", "f06"]
})

glossary.append({
    "id": "g06",
    "title": "委托代理问题（Principal-Agent Problem）",
    "type": "glossary",
    "source_chapter": "ch005 / 第2章",
    "source_quote": "官僚组织在委托代理关系中，中央与地方政府双方利益目标不同、信息不对称，在漫长的行政链条中，只能实行层层节制。",
    "summary": "委托代理问题是组织经济学核心概念：委托人（中央）与代理人（地方）利益不完全一致，且代理人掌握更多信息。在中国，这种委托代理问题因治理规模庞大、层级众多、信息失真严重而尤为突出，构成了中国国家治理的基本困境。",
    "keywords": ["委托代理", "信息不对称", "激励机制", "代理问题"],
    "v3_pass": True,
    "v3_reason": "将组织经济学核心概念引入中国政府分析，为理解上下级张力提供了分析工具。",
    "v2_scenario": "中央制定减排目标时，地方可能掌握更多关于本地实际排放情况的信息，存在信息不对称，委托代理问题由此产生。",
    "related": ["f01", "p04", "f09"]
})

glossary.append({
    "id": "g07",
    "title": "一统体制与有效治理的矛盾",
    "type": "glossary",
    "source_chapter": "ch004 / 第1章",
    "source_quote": "中国国家治理的一个深刻矛盾是一统体制与有效治理之间的矛盾，集中表现在中央管辖权与地方治理权间的紧张和不兼容。",
    "summary": "这是全书的核心矛盾命题：中央一统性要求权力向上集中，地方有效性要求权力下沉到有信息优势的下级。一统体制越强，有效治理越弱；反之亦然。这一矛盾无法根本解决，只能在动态中寻找暂时平衡。",
    "keywords": ["一统体制", "有效治理", "中央地方关系", "基本矛盾"],
    "v3_pass": True,
    "v3_reason": "全书的核心命题，理解所有制度机制的出发点。",
    "v2_scenario": "理解中央为何在'集权-放权'间摇摆：每轮放权后地方失控触发新一轮集权，集权后地方活力下降又触发再放权。",
    "related": ["f04", "f01", "p01"]
})

# ============================================================
# INSIGHTS
# ============================================================
insights = []

insights.append({
    "id": "i01",
    "title": "中国国家治理的深层逻辑是应对一统与治理的矛盾",
    "type": "insight",
    "source_chapter": "ch004 / 第1章",
    "source_line": 1,
    "source_quote": "国家治理逻辑在很大程度上是针对一统体制与有效治理之间的矛盾而演化发展起来的，体现在一整套制度设施和应对机制之上。",
    "summary": "作者的核心洞察：中国政府的所有制度安排——官僚制度、观念制度、运动型治理、逐级代理——都是为了应对'一统体制要求权力集中'与'有效治理要求权力下沉'这一根本矛盾的产物。这些制度不是偶然设计，而是历史演化的解决之道。",
    "keywords": ["制度演化", "矛盾应对", "治理逻辑"],
    "v3_pass": True,
    "v3_reason": "这是作者的核心论点，提供了理解中国国家治理的整体框架。",
    "v2_scenario": "理解为何中国会发展出'巡视组'制度：因为常规官僚体系无法有效监督地方，需要通过跨越常规层级的非常规机制来纠偏。",
    "related": ["f04", "f02", "g07"]
})

insights.append({
    "id": "i02",
    "title": "基层官员的'变通'不是腐败而是理性应对",
    "type": "insight",
    "source_chapter": "ch010 / 第7章",
    "source_line": 1,
    "source_quote": "基层政府在执行过程中的灵活变通和共谋行为不是官员品质问题，而是组织在特定制度环境下的理性应对。",
    "summary": "传统观点将基层变通、共谋视为腐败或执行不力。作者的洞察是：这些行为是在特定制度约束下的理性选择。当正式制度（一统体制的要求）与实际可行（有效治理的要求）之间存在鸿沟时，非正式行为是填补这一鸿沟的理性手段。",
    "keywords": ["变通", "理性行为", "制度约束", "非正式"],
    "v3_pass": True,
    "v3_reason": "颠覆了'变通即腐败'的简单判断，提供了理解中国基层政治的新视角。",
    "v2_scenario": "理解地方官员的'数字注水'：不是简单的道德问题，而是在考核压力下的理性选择。",
    "related": ["f06", "f08", "p07"]
})

insights.append({
    "id": "i03",
    "title": "中国历史上的治理危机都源于无法平衡两种需求",
    "type": "insight",
    "source_chapter": "ch003 / 第12章 结语",
    "source_line": 1,
    "source_quote": "中国历史上帝国治理的基本特征是稳定、停滞与循环：兴盛是因为暂时找到了平衡点，衰落是因为平衡被打破。这一循环在中国历史上反复出现。",
    "summary": "作者的历史洞察：中国帝国的治理危机不是源于外敌入侵或农民起义，而是源于一统体制与有效治理之间的平衡被打破——要么中央过于集权导致体制僵死，要么地方过于分权导致割据分裂。当代中国的挑战同样是：在现代条件下重新寻找这一平衡。",
    "keywords": ["历史循环", "帝国治理", "平衡点"],
    "v3_pass": True,
    "v3_reason": "将当代治理问题置入中国大历史框架，提供了纵向视角。",
    "v2_scenario": "理解为何中国必须维持'稳定压倒一切'：历史上平衡被打破的后果（农民起义、政权崩溃）是执政者的深层忧虑。",
    "related": ["g07", "f04", "f09"]
})

# ============================================================
# Write candidates to files
# ============================================================
def write_candidates(filepath, items):
    with open(filepath, "w", encoding="utf-8") as f:
        for i, item in enumerate(items):
            f.write(f"- id: {item['id']}\n")
            f.write(f"  title: {item['title']}\n")
            f.write(f"  type: {item['type']}\n")
            f.write(f"  source_chapter: {item['source_chapter']}\n")
            f.write(f"  source_line: {item.get('source_line', 1)}\n")
            f.write(f"  source_quote: \"{item['source_quote']}\"\n")
            f.write(f"  summary: \"{item['summary']}\"\n")
            f.write(f"  keywords: [{', '.join(item['keywords'])}]\n")
            f.write(f"  v3_pass: {item['v3_pass']}\n")
            f.write(f"  v3_reason: \"{item['v3_reason']}\"\n")
            f.write(f"  v2_scenario: \"{item['v2_scenario']}\"\n")
            if item.get('related'):
                f.write(f"  related: [{', '.join(item['related'])}]\n")
            if item.get('linked_method_hint'):
                f.write(f"  linked_method_hint: \"{item['linked_method_hint']}\"\n")
            if i < len(items) - 1:
                f.write("\n---\n\n")

write_candidates(os.path.join(CANDIDATES_DIR, "frameworks.md"), frameworks)
write_candidates(os.path.join(CANDIDATES_DIR, "principles.md"), principles)
write_candidates(os.path.join(CANDIDATES_DIR, "cases.md"), cases)
write_candidates(os.path.join(CANDIDATES_DIR, "boundaries.md"), boundaries)
write_candidates(os.path.join(CANDIDATES_DIR, "glossary.md"), glossary)
write_candidates(os.path.join(CANDIDATES_DIR, "insights.md"), insights)

print(f"\nWrote:")
print(f"  frameworks: {len(frameworks)}")
print(f"  principles: {len(principles)}")
print(f"  cases: {len(cases)}")
print(f"  boundaries: {len(boundaries)}")
print(f"  glossary: {len(glossary)}")
print(f"  insights: {len(insights)}")
print(f"  Total: {sum([len(frameworks), len(principles), len(cases), len(boundaries), len(glossary), len(insights)])}")
# 公司分析数据覆盖率审计

> 最后验证：2026-06-04（双环传动案例）

## 演进历史

| 分析 | 版本 | jw-investment-data占比 | 关键变化 |
|------|------|----------------------|---------|
| 荣盛石化 | v3.29 | ~10% | comprehensive未接入 |
| 宏桥控股 | v3.29 | ~10% | 脚本权限问题 |
| 拓普集团 | v3.31 | ~70% | v3.7 comprehensive（6源） |
| 双环传动 | v3.32 | ~85% | v3.8 comprehensive（11源） |

## comprehensive 11源覆盖

| 数据源 | 覆盖Step | 成功率 |
|--------|---------|--------|
| adata_finance（43列） | Step 2 | 100% |
| forecast（业绩预告） | Step 1.4 | 100% |
| express（业绩快报） | Step 2 | ~70% |
| operation（营运能力） | Step 2 | 100% |
| shares（股本变动） | Step 0 | 100% |
| concept（概念板块） | Step 3 | 100% |
| plate（板块归属） | Step 0,3 | 100% |
| north_flow（北向资金） | Step 5 | 100% |
| stock_lifting（解禁） | Step 5 | 100% |
| popularity（人气榜） | Step 6 | ~50% |
| index_membership（指数） | Step 0 | 100% |

## 仍需 web search（~12-15%）

- 管理层姓名/简历/薪酬（无API）
- 股东关系/一致行动人（需文本解析）
- 竞争对手财务对比（需跨公司聚合）
- 行业细分市占率（第三方数据）
- 机构评级/目标价（券商研报非公开）
- 公司公告详情（需文本理解）

## 天花板

comprehensive已覆盖85-88%。剩余12-15%无结构化API，web search是唯一途径。

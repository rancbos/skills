# jw-maoism v7 changelog

## v7 (2026-05-31) — Optimization pass

### Fixed
- Changelog version gap: v6→v7 now documented
- SKILL.md vs interaction-enhancements.md deduplication: removed redundant "禁用表达" duplicate, kept SKILL.md inline quick-ref as canonical
- Evals: added `expectations` field to all 7 test cases for automated grading
- Complexity judgment: added hard rules (survival problems, 3+ stakeholders, prediction+risk control → always complex) to prevent misclassification
- Anti-pattern #9: aligned wording with new hard rules

### Verified
- All 9 reference files present on disk
- YAML frontmatter valid
- 分层决策 (simple/medium/complex) flow intact
- 反模式清单 (8 items) intact
- Self-check list 3/6/9 scaling intact

## v6 (2026-05-31) — Architectural review + improvements

### Added
- **判断力培养** section: 5 principles for developing judgment under uncertainty
- **常见反模式** table: 7 common analysis mistakes with corrections
- **时机判断** in action plan step: when to accelerate/wait/retreat
- **分层决策** table at flow header: simple(3步) → medium(5步) → complex(7步)
- **中途退出条件**: stop and ask when info insufficient, loop back if main contradiction wrong
- **Reference usage guidance**: table mapping each reference file to trigger conditions
- **Language style** re-added after patch collision removed it

### Changed
- Self-check list scaled by complexity: 3 (simple) → 6 (medium) → 9 (complex), was fixed 12
- Output spec simplified: references flow header's complexity table instead of duplicating it
- Methodology depth references now include trigger conditions for each file

### Design principles captured
- Full design patterns document: `skill-creator/references/analytical-framework-design.md`
- Covers: hierarchical model structure, model-to-flow mapping, auxiliary model completeness, judgment dimension, timing sense, contradiction reframing, anti-patterns, self-check scaling, reference usage guidance

## v5 (2026-05-31) — 10 fixes from reference skill comparison
- Unified front model upgraded to 8th core model
- Auxiliary models given full "operation + enhancement + limitation" structure
- Each flow step annotated with which models to invoke
- Problem type → model selection mapping table
- Contradiction reframing framework expanded
- "不触发" conditions in frontmatter
- Flow step 6 can loop back to step 2
- Concentrated forces merged into rural-encircling-cities
- Standalone quotes section removed, integrated into models
- Output length calibration added

## v4 (2026-05-31) — Mao as primary framework
- Restructured from 10 flat models to 6 Mao core + 5 auxiliary
- Mao's thought as backbone, Deng/Xi/Marx as enhancements

## v3 (2026-05-31) — Deep research integration
- Added Capital deep tools (10 economic analysis tools)
- Added Xi Jinping deep wisdom (12 practical points)
- Added life wisdom section (15 quotes from 3 thinkers)

## v2 (2026-05-30) — Four thinkers integration
- Expanded from Mao-only to Mao+Deng+Xi+Marx
- 10 core models, 12 decision heuristics

## v1 (2026-05-30) — Initial creation
- 6 core models from Mao's thought
- 7-step analysis flow
- Wisdom elder persona

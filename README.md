# GDD-Literature-2024-2026｜肠道靶向药物递送载体文献库

围绕「药物递送载体 × 肠道（gut / intestine / colon）靶向开发生物医学应用」方向，
对 **2024-01-01 ~ 2026-10-09** 进行的全量回顾检索成果（按年为单位执行）。

- 数据源：Europe PMC + arXiv（检索式见 `tools/gdd_search*.py`）
- 期刊白名单：严格限定第一/第二梯队共 20 本（Nature、Science、Nat Rev Drug Discov、
  Chem Rev、Chem Soc Rev、Nat Nanotechnol、Nat Mater、Nat Biomed Eng、Adv Mater、Angew Chem；
  J Control Release、Adv Drug Deliv Rev、ACS Nano、Nano Today、Biomaterials、Matter、
  Nat Commun、Sci Adv、Nano Lett、JACS），白名单外不检索
- 配套 Skill：`gut-dd-literature-pipeline`（由 `elm-literature-pipeline` 派生，含完整流水线规范）

## 核心数据

| 环节 | 数量 |
|---|---|
| 候选全库（去重后） | 4,716 篇 |
| 白名单保留（T1 319 / T2 1,988） | 2,308 篇 |
| 相关度剔除（摘要核实离题） | 1 篇 |
| **最终保留（DOI 100% 补全）** | **2,307 篇** |
| 其中肠道相关核心集 | 486 篇 |

年度分布：2024 年 758 篇 ｜ 2025 年 974 篇 ｜ 2026 年（至 10-09）575 篇。

## 目录结构

```
├── 01_PDF/                    # PDF 全文（版权原因不入库，见 .gitignore）
├── 02_BibTeX/                 # 按年 BibTeX 库 + 规范化命名清单（Zotero 可直接导入）
│   ├── GDD_2024_library.bib
│   ├── GDD_2025_library.bib
│   ├── GDD_2026_library.bib
│   └── naming_manifest_<年>.csv
├── 03_Reports/                # 汇总报告与清单
│   ├── 年度检索汇总报告.md
│   ├── 肠道相关文献清单.md     # 486 篇核心集（标注研究/综述 + DOI）
│   ├── 手动下载Checklist.md   # 三态下载清单
│   └── exclusion_log.md       # 白名单外期刊计数 + 相关度剔除理由
├── tools/                     # 流水线脚本（gdd_*.py，可重跑）
├── raw/                       # API 原始响应（本地保留，不入库，可重新抓取）
├── literature_database.json   # 最终保留库（2,307 篇）
├── literature_database_all.json  # 全量归档（含白名单外计数记录）
└── relevance_drops.json       # 相关度剔除/标注清单
```

## 复现检索

```bash
cd tools
python gdd_search.py --dir .. --from 2024-01-01 --to 2024-12-31   # 宽检索 6 组主题
python gdd_search_targeted.py --dir .. --from 2024-01-01 --to 2024-12-31  # 白名单定向精检
python gdd_build_db.py --dir .. --merge
python gdd_filter_journals.py --dir .. --stage first   # T1/T2 白名单筛选
python gdd_fix_dois.py --dir ..                        # CrossRef DOI 补全
python gdd_filter_journals.py --dir .. --stage final   # 终筛
python gdd_relevance_filter.py --dir ..                # 相关度剔除
python gdd_export_bib.py --dir .. --prefix GDD_2024 --year 2024
python gdd_rebuild_checklist.py --dir .. --window "2024-01-01 至 2026-10-09（回顾补齐）"
```

依赖：Python 3.10+，仅用标准库（urllib/json），无需额外安装。

## GitHub 说明

- 远程仓库：`https://github.com/DediCationMeng/Gut-Drug-Delivery-References`
- 上传内容：文献数据库、BibTeX、报告、检索脚本（约 25 MB）
- **不上传**：PDF 全文（版权）、`raw/` 中间数据、本地备份（见 `.gitignore`）

```bash
git remote add origin https://github.com/DediCationMeng/Gut-Drug-Delivery-References.git
git branch -M main
git push -u origin main
```

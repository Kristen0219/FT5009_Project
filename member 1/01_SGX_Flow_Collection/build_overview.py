"""Create dataset documentation from the recorded extraction audit."""
from pathlib import Path
import csv,json
from collections import Counter
ROOT=Path(__file__).resolve().parent

def main():
 s=json.loads((ROOT/'summary.json').read_text());checks=list(csv.DictReader((ROOT/'report_checks.csv').open()))
 anomalies=[r for r in checks if r.get('timing_status')=='review_required']
 reviews=[r for r in checks if r.get('extraction_status')!='parsed_40_rows' or r.get('title_sheet_week_match')=='review_required' or r.get('rank_order_review')]
 with (ROOT/'timing_anomalies.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=checks[0].keys());w.writeheader();w.writerows(anomalies)
 gaps=list(csv.DictReader((ROOT/'weeks_to_investigate.csv').open()))
 lines=['# SGX Weekly Top 10 数据收集结果','',
 '这是 Member 1 的真实资金流数据集和来源审计，不包含日股价、成交量、基准或策略收益。',
 '',f"已扫描官方 Fund Flow Tracker 主分类全部 {s['archive_entries']} 条目录记录，并在缺周日期范围补查全部分类。按页面列示发布日期 2019-01-01 至 2026-09-30、且标题为周度资金流报告，筛出 {s['download_attempts']} 条。", 
 f"成功下载 {s['downloaded']} 份；严格识别四张 Top 10 表的文件 {s['reports_parsed']} 份；提取 {s['signal_rows']:,} 行；涉及 {s['unique_sgx_codes']} 个不同 SGX 代码。",'',
 '| 页面发布日期年份 | 报告条数 |','|---|---:|']
 lines += [f'| {y} | {n} |' for y,n in sorted(s['by_publication_year'].items())]
 lines += ['', '## 文件怎么用','',
 '- `raw/`：官方原始 Excel，保留原字节。',
 '- `archive_all.json`：主分类 5 页的 472 条原始标题、日期和链接。`supplementary_weekly_reports.json` 是跨分类补回的 1 份周报；`gap_search_all_categories.json` 保留缺周日期范围的全部分类搜索结果。',
 '- `download_manifest_combined.json`：本次下载结果、文件路径、SHA256。',
 '- `flows_extracted.csv`：全部提取信号，含报告 ID、原页面日期、周标签、方向、排名、金额、股票代码/名称、来源 URL/单元格。',
 '- `report_checks.csv`：逐报告结构检查、日期问题、标题与表内日期比较、排名顺序检查。',
 '- `security_codes_to_map.csv`：给行情数据收集用的股票代码清单；仍需补 ISIN、币种、历史映射、上市/退市记录。',
 '- `timing_anomalies.csv`：页面列示日期不晚于所覆盖周推定周五的条目。',
 '- `weeks_to_investigate.csv`：未在目录标题中发现的周标签；不能视为零流量。',
 '- `excluded_archive_entries.json`：排除项与原因，含月度、YTD、其他报告与日期范围外条目。',
 '', '## 数据定义与核验','',
 '只取 `Weekly Top 10` 工作表的 institutional buy/sell、retail buy/sell 四张表。不混用其他工作表、月度排名或 YTD 排名。每张表保留原始顺序为 rank，金额单位 S$ million，买入为正、卖出为负。保留文件存储精度。Top 10 金额之和只是该表的合计，不能称为整个市场净流量。',
 '', '程序逐文件检查：4 个表头、每表 10 个有效证券和金额、S$M 单位、股票代码列、正确正负号、同一投资者名单无重复/方向冲突。另检查榜单排序、表内周标签与目录标题是否一致。结构通过不等于原始供应商数据无误，也不等于历史发布日期已独立验证。',
 '', '## 回测前必须解决的问题','',
 f"1. 日期异常 {len(anomalies)} 条："]
 lines += [f"   - 页面日期 {r['publication_date']}；表内周起点 {r['week_start']}；{r['report_id']}。" for r in anomalies]
 lines += ['', '这些条目在覆盖周结束前就显示为发布，不能直接用于交易时点。保留原值，须查实际发布证据；不要悄悄把它们改成下周一并声称已验证。正常条目也仅来自当前网页元数据，需披露缺乏历史发布时间/版本记录的限制。',
 '',f"2. 有 {len(gaps)} 个周标签需调查："+', '.join(r['expected_week_start'] for r in gaps)+'.',
 '主分类扫描后，额外补查缺周日期范围的全部分类，补回 2021-04-05 那周的一份 Institutional Newsletter 分类周报。2020-05-26 和 2020-08-11 的周二标签已归入同一 ISO 自然周，不再计为缺周。剩余缺口不证明报告从未发布，外部档案仍可能保留。月度/YTD表不能填补缺失的 Weekly Top 10。',
 '', '3. week_start 保留官方周标签日期；iso_week_start 统一为该自然周周一。week_end_derived = iso_week_start + 4 个日历日，仅是周五推定值。遇到假期时不得声称为真实最后交易日；后续以 SGX 交易日历核实。按“发布日期”取样，2019-01-07 发布且覆盖 2018-12-31 那周的报告已纳入。',
 '', '4. 代码清单不是稳定证券主表。同一代码可能改名、重组或被重新使用；不同代码也可能是同一历史证券。`SGX_代码` 是临时 ID，不可未经映射直接完成公司行动处理。非 SGD 股票需要汇率转换；不能因为资金流以 S$M 报告，就认定其股价币种也是 SGD。',
 '', '5. 尚未取得 daily prices、share volume、SGD total-return series、benchmark 和历史借券信息。下一步用代码清单从有权限的学校行情数据库获取，包括已退市证券和 2019 前的足够历史。至少 500 个对齐历史日收益的覆盖需要逐资产核验。',
 '', '因此本 CSV 是经过结构检查的 extracted data，不是已经完全清洗、可直接用于无前视回测的最终输入。不要把本次数据收集结果写成“全组作业完成”。',
 '', '## 复现','', '```bash','python collect_history.py','python parse_history.py','python coverage.py','python build_overview.py','python verify_dataset.py','```',
 '', '下载程序仅使用归档目录中实际观察到的链接，不猜测文件 URL。文件 ID 为来源 URL 的 SHA256 前 12 位。可选 `--reverse` 是同样目录的倒序断点下载，原始文件缓存在 raw；解析程序合并下载回执。解析与审计可离线运行（Python 标准库）。',
 '', '目录获取：通过用户授权的浏览器查看 SGX 页面，将每条可见报告标题、列示日期与下载链接记录在 archive_all.json；该网页快照是数据来源输入，不包含自动控制浏览器的代码。',
 '', '来源：https://www.sgx.com/stock-exchange/data-reports?reportType=203 。访问/下载日期：2026-10-21。逐文件 URL 见 CSV 和 manifest。',
 '', 'AI assistance：ChatGPT assisted with source collection, extraction code and documentation. The group should review the recorded timing anomalies, data coverage, identifiers and assumptions before reporting results.']
 (ROOT/'README.md').write_text('\n'.join(lines)+'\n')
 print('README generated; remaining extraction review records:',len(reviews))
if __name__=='__main__':main()

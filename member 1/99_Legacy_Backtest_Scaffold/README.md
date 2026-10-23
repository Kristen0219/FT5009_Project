> LEGACY REFERENCE: superseded by Kelly/02_Baseline_Backtesting/. Do not use these instructions for the current baseline.

# FT5009 — Member 1: Data & Baseline Backtesting

## 状态（请先读）
已实现：两个基础策略的回测引擎、数据格式、报告下载工具、输入检查、会计测试、方法章节草稿和组员交接规范。
**真实资金流已另收集于 `../data/sgx`：399 份报告、15,960 条信号。仍缺日股价/成交量/基准、历史证券映射及日期异常核实。本目录 input CSV 仍是字段模板，尚未把待核实数据接入正式回测。没有编造策略收益。**

作业范围：报告发布日期 2019-01-01 至 2026-09-30；每日绩效计算至 2026-09-30。不要纳入截止日前观察、但截止日后才发布的报告。截止日期为 2026-10-30 23:59:59（新加坡时间）。最终全组报告最多 10 页，含图与 references；本包不是全组最终 submission ZIP。

## 你负责完成的流程

1. SGX 官方入口：https://www.sgx.com/stock-exchange/data-reports?reportType=203 。逐页查找历史周报，保留原始 PDF。2026 年和早期版本标题可能不同。不要将月度、YTD Top 100 或 STI constituent 表混作 Weekly Top 10。
2. 填 `reports.csv`：每份报告一行，记录报告覆盖周、实际发布日期、直接 PDF URL、状态。状态为 complete / missing / incomplete。无法确定发布日期的报告不能先入策略。发布日期≠week_end；不要一律假定周一发布。
3. 可运行 `python collect_reports.py` 下载已核验 URL 并计算 SHA256。再用 `pdftotext -layout data/raw/xxx.pdf ...` 辅助提取四张 Weekly Top 10 表，人工复核标题、币种、代码、方向、负号与排名。脚本没有实现未经验证的全历史自动表格解析。
4. 四张表分别是 institutional buy、institutional sell、retail buy、retail sell。将其整理进 `flows.csv`。每份通常 40 行；如原文少于 10 支，保留实际行数并说明。买入为正，卖出为负；单位统一 S$ million。没出现在表里代表 unreported，不能补成零。
5. 从学校可用的 Bloomberg / LSEG / Datastream 或可验证的历史行情源取得所有历年信号股票，而非仅今天仍上市股票。保存原始导出和字段说明。需要 daily close、share volume、SGD total-return index，以及基准序列。初始风险估计至少需要 500 个对齐日收益，因此建议从 2016-01-01 开始拉取，核验实际有效窗口。起始日期本身不能保证每个新股都有 500 日。
6. 统一 `security_id`：使用稳定内部 ID + ISIN/上市实体映射，股票简称不能当主键。维护代码变更、重组、退市、换股、股息/拆股记录。`security_master.csv` 与 `events.csv` 是人工治理记录，回测不会自动推断公司行动。
7. 对总回报序列、SGD 转换和成交量逐项核对后运行 audit，再回测。遇到已持有股票缺报价/退市，代码会停止；需要从可靠来源补充经济回报/结算价及事件说明，不能删掉这段或默认为零。
8. 将 output 交给 Member 2 / 3。全历史数据核验完成后，更新报告草稿中的实际覆盖与排除数字，再与组员合并。

## 安装与运行

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python audit.py --input data/input
python backtest.py --input data/input --output output
```

测试使用内部构造的小样本，只验证执行滞后、成本、长短盈亏、缺价拒绝和周末借券计息。空输入会明确报错。运行不需要实时网络；提交数据齐备后可以离线复现。

## 固定的 baseline 规则（建模选择，不是题目指定参数）

- 两个名称：Smart Retail Flow FT5009 / Smart Insti Flow FT5009。各初始 S$1,000,000。
- 每次新报告：跟随该类投资者 Top 10 net buy 做多、Top 10 net sell 做空。不按 flow 大小加权，避免大市值股票主导。
- 多头目标 49%，空头目标 49%，单一股票每边不超过 NAV 10%。通常 10 支各 4.9%，gross 98%，net 0%。2% 留作成本缓冲。若实际表更短则等权、受 10% cap；不可交易标的对应额度留在现金，不从其他表补选、不重新分摊。
- 在**实际本地发布日期严格之后的第一个 SGX 交易日收盘**调仓；忽略具体发布时间，统一保守延迟。此处用收盘价代理执行价，不声称成交在真实开盘或 VWAP。新权重从下一日收益起生效。
- 用基准序列的交易日作为交易日历；基准数据必须覆盖真实 SGX 交易日，不能静默丢掉有行情的日子。发布频率通常周度；若档案缺报告必须调查并披露。已在 inventory 标注 missing/incomplete 的报告会阻止运行；尚未录入 inventory 的漏报仍需人工发现。不能把漏采报告导致的长持有误称为已验证策略。
- 新报告覆盖旧目标：不在新名单的持仓退出，保留名单的调回目标，反方向信号反手；两份报告若映射到同一执行日则报错，需显式处理。结尾按市值计价，不强制平仓。
- 总回报指数用于每日价格/分红/拆股一致的经济回报。回测采用 fractional synthetic total-return units；不是实际逐笔股数或 SGX board-lot 执行模拟。分红视为再投资，空头承担对应 total return；需在局限中披露此代理。close 为未复权 SGD 收盘价，仅用于估计交易股数和成交量参与率。
- 调仓时按当日 NAV 计算目标金额，实际买卖金额为目标减调仓前市值。单边成本假设 20 bps × |成交金额|，gross 为 0 成本和 0 借券成本，net 为 20 bps + 年化 3% 借券费，double_cost 为 40 bps + 相同借券费。这些是假设，须用券商费用/可借券资料检验；不是已取得的历史报价。
- 现金余额 = 初始资本 − 净买入 − 费用；空头卖出款包含在现金，但全部视为受限抵押、不再用于额外杠杆，不付现金/抵押利息。gross exposure 与单名限制在调仓目标时适用，期间随市场漂移，非每日硬性上限。费用会使调仓后权重略高于目标。
- `short_available` 必须按当时信息录入；若取不到历史借券数据，可全设为 1 但必须明确写成“假设全部可借券”的假设场景，并另做可用性敏感性分析。不要伪称已验证。3% 借券费按前一收盘空头名义金额和日历天数/365 扣除（含周末），忽略召回、挤仓、融资限制。可借券状态仅在调仓时检查。
- 对 volume=0 或无执行报价的新信号不交易并记录；已持有股票的经济回报/退出报价缺失则停止，要求明确处理。停牌不能简单看作退市，退市不能随意按零收回或最后价平仓。
- 成交量参与率 = |成交金额| / (当日未复权 close × 当日 share volume)。这是事后可行性分析，不作为当日收盘前已知过滤条件；代码无市场冲击或参与率限额。

## 数据文件

| 文件 | 必要内容 |
|---|---|
| reports.csv | report_id, week_end, publication_date, status, source_url, local_file, sha256, notes |
| flows.csv | report_id, publication_date, investor=retail/institutional, side=buy/sell, security_id, rank, flow_sgd_m（有符号）, source_page |
| prices.csv | date, security_id, close（SGD未复权）, total_return_index（SGD总回报）, volume（股数）, currency=SGD, short_available=0/1, source_url |
| benchmark.csv | date, total_return_index, source_url；建议 STI total return 或 STI ETF 的复权总回报代理，注明费用/跟踪误差与净多头基准局限 |
| security_master.csv | 稳定 ID、ISIN、历史代码、公司名、上市/退市日、行情源代码等 |
| events.csv | 公司行动、停牌、退市、处理方法与证据 |

海外币种上市证券：先将总回报资产价值按当日 SGD 汇率转换后再计算日收益；不能只改 currency 标签。记录汇率来源和日期对齐。题目不要求排除非 SGD 证券；若选择排除，要统一规则并披露偏差。

## 给组员的接口

`retail_net_daily.csv` / `institutional_net_daily.csv`：date, nav, daily_return, cost_sgd, borrow_sgd, turnover, cash_sgd, gross_exposure, net_exposure。turnover 是单边买卖绝对额合计/NAV；不能再未经说明除以 2。

`*_holdings.csv`：每日 start_weight 为该日收益发生前的上一收盘权重，end_weight/end_value_sgd 为当日收盘（含调仓后）持仓。Member 3 对 t+1 的 VaR 使用 t 收盘 end_weight 与 NAV，仅用截至 t 的前 500 个对齐历史日收益；不要使用 t+1 的真实回报。空头保持负号，不用组合自身过去收益代替当前持仓历史模拟。500 日 insufficient history 要统一处理并报告 coverage，不能给新股补零。

`asset_returns_aligned.csv`：包含 2019 前历史，日历与 benchmark 对齐、缺失值保留为空。Member 3 必须检查当前持仓的联合有效窗口，不能拿每个股票不同时期的 500 个样本拼接。

`*_trades.csv`：日期、报告、证券、成交名义金额、成本、估算股数、成交量参与率。`*_exclusions.csv`：未成交原因。空记录输出可能为空文件，组员读取前检查文件大小。

Member 2：增强策略调用同一个 simulate 或复用同一日收益/成本会计，保持执行时点与曝光规则可比；三个子时期的收益从完整回测切片，不能每个子时期重新初始化并改变持仓。gross/net/double_cost 各为独立 NAV 路径，金额略有差异是成本影响复利的结果。

## 原始数据与来源记录

SGX 资金流收集成果见 ../Kelly/01_SGX_Flow_Collection/README.md；该分类可见报告及跨分类补充已保存，另列 5 个未发现周报的自然周和 3 条日期异常。环境中一次 Yahoo 日行情请求收到 HTTP 429；没有将失败请求当作已收集数据。付费数据库的学校访问权限需由组员在可用账号下导出。本包没有内置第三方未经验证的数据替代品。

务必保留：原始文件、下载/导出日期、字段描述、覆盖区间、缺失报告列表、所有排除与处理记录。`audit.py` 是辅助检查，不证明档案完整，也不自动核验原文转录。

AI assistance disclosure 建议：We used ChatGPT to assist with drafting the data schema, baseline backtesting implementation and documentation. All source data, methodology choices and reported results were independently verified by the group. 最后一句仅在你们确实完成核验后使用。

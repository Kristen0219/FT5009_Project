# Member 2 — 策略增强与绩效评估

本目录完成 FT5009 AY2026/27 作业 **Part 3、Part 4，以及本人对应的 Part 6 代码与报告章节**。直接复用 Member 1 当前版本的样本和原始回测引擎，原 `member 1/` 下的文件不会被改写。不混用早期 Y92/YF8 全样本排除版本。

## 查看交付结果

- [英文报告章节](results/MEMBER2_REPORT.md)：规则依据、六项绩效指标、三个指定子期间、成本压力测试、流动性、结论及限制。
- [三页 A4 PDF 报告章节](results/MEMBER2_REPORT_A4.pdf)：可供 Member 3 合并进最终报告；全组最终 PDF 仍须不超过 10 页。
- [净收益与回撤图](results/figures/net_returns_drawdowns.png)、[成本比较图](results/figures/cost_stress.png)：另附可缩放 PDF 图。
- [完整绩效表](results/performance.csv)：三策略 × 毛收益/净收益/双倍交易成本 × 全期/三个子期间，另有基准。
- [流动性汇总](results/liquidity_summary.csv)：成交参与率、滞后 21 日 ADV 参与率及超过 1%/5% 的情况。
- [逐笔成交和流动性](results/trades_and_liquidity.csv.gz)、各情景每日 NAV/收益/成本、逐信号增强决策均可核查。
- [Member 3 风险交接](results/risk_handoff/README.md)：三策略净持仓、隔离异常后的资产收益和严格 500 日窗口覆盖表。
- [验证记录](results/validation.json)：数据哈希、基线逐日匹配、会计与执行日期检查、版本和风险覆盖缺口。

## 一键离线复现

在仓库根目录运行；路径有空格，必须保留引号。建议 Python **3.12**，以下依赖锁定版本已实际验证：

```bash
python3 -m venv /tmp/ft5009-member2-venv
source /tmp/ft5009-member2-venv/bin/activate
python -m pip install -r "member 2/requirements-lock.txt"
python "member 2/run_member2.py"
```

依赖安装需联网；数据、源报告、增强、绩效、图表和报告生成完全离线。首次运行会将 Member 1 文件复制到被 Git 忽略的 `member 2/work/`，校验解压数据并运行其完整复现、10 项测试及独立审计，再执行全部九条策略路径和 Member 2 测试。日志位于 `member 2/work/member1_reproduction.log`。数据处理和回测需要几分钟，磁盘预留 1 GB 以上。

后续运行仅在源文件哈希和准备数据哈希完全匹配时复用缓存。强制重建：

```bash
python "member 2/run_member2.py" --rebuild-inputs
```

旧工作副本会留存为 `work/previous-*`，不会删除用户文件；多次强制重建会增加磁盘占用。`work/` 不提交 GitHub。程序重建本目录的 `results/`，如有人手工修改这些生成文件，应先另存。

仅运行 Member 2 单元测试：

```bash
python -m unittest discover -s "member 2/tests" -v
```

`requirements.txt` 给出兼容范围；`requirements-lock.txt` 用于重现本次环境。不同 Python/平台可能需要另行选择兼容依赖，并核对数值结果。

## 增强规则（先固定，再运行）

采用**126 个交易日简单移动平均（SMA）趋势确认**：用发布日期严格之前最近一个基准交易日的 SGD 总收益指数，与截至该日的最近 126 个交易日指数均值比较。买入信号要求指数高于均线，卖出信号要求低于均线；126 个指数值中有缺失、历史不足或指数等于均线均不交易。没有试参或以全样本结果优化参数。

每边原有十个 4.9% 槽位保留；拒绝的槽位留现金，不向剩余股票重分配。退出、无法成交冻结、49% 单边预算、10% 单股上限、发布日期后的首次收盘成交、现金/抵押品、手续费和借券等全部沿用 Member 1。现有代码不以修改交易量或价格的方法实现过滤。

已核对你上传的**第 8 讲 PDF 第 16 页（SMA）及第 21 页（价格与均线交易规则）**。课堂示例是短窗口、只做多/现金；这里明确改编为 126 个日频观测、SGD 总收益指数和机构信号的对称多空过滤，仍以每周报告触发交易。第 2 讲的信息时点及第 7 讲的流动性概念也在实现与报告中对应。详见 [讲义对应说明](LECTURE_ALIGNMENT.md)。讲义本身不会重复上传到 GitHub。

## 分工边界与提交前人工事项

- 本目录实际实现 Parts 3–4，不宣称已完成 Member 3 的 Part 5（21 日滚动波动率及 99% 历史模拟 VaR）。只提供其必要的持仓、收益和覆盖交接数据。
- 三页 PDF 是 Member 2 章节，不是最终全组报告。Member 3 仍需整合全部章节、姓名/学号/贡献、完整参考文献，并检查 A4、最多 10 页及 Canvas 最终 ZIP 命名。
- 结果仅适用于 Member 1 的固定、可用历史样本；不代表无偏的全市场可投资业绩。异常收益、缺失历史、当前供应商数据版本、做空可得性和交易冲击等限制仍须披露。
- 如增强后收益下降，报告照实呈现，不为提高收益而事后调参。比较收益时同时检查风险、暴露、成本与分期稳定性。
- 已披露 OpenAI Codex 的代码、分析和写作辅助。最终提交者应核验计算与论述并承担责任。

作业映射与文件说明见 [REQUIREMENTS_CHECKLIST.md](REQUIREMENTS_CHECKLIST.md)。

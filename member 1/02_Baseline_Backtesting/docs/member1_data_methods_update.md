# Current data and baseline methods

This supersedes the earlier retrospective Y92/YF8 exclusion text. The report-ready methods are in ../../FT5009_Member1_Report_Audited.docx. The requirements, evidence, limitations and update instructions are in ../../REQUIREMENTS_AUDIT.md.

The default scenario is FIXED_PRE2019_ELIGIBILITY_BASELINE. Only returns before 2019 determine membership: at least 500 valid aligned pre-period returns and no pre-period absolute return above 50%. The resulting 125 canonical histories cover 127 source codes. Missing original histories (66 codes), inadequate pre-period history (30 canonical histories) and flagged pre-period source quality (13 canonical histories) are distinct reasons. Later listings are excluded consistently rather than admitted using future history.

Input signals retain all ten slots per list; missing/ineligible slots stay cash. Screen failures and later post-2018 review observations are not claims that every large return is wrong. The screen and fixed sample can exclude legitimate volatility and create sample bias. Current vendor data and current archive metadata do not establish historical data vintages.

The engine's existing 49% long/49% short sizing, S$1m initial capital, release lag, frozen-holding budget, costs and borrow rules are unchanged. Only the data eligibility and explicit risk-history handoff differ. Previous results are retained for provenance, not for mixing into the final comparison.

For VaR, asset_returns_for_var.csv separately quarantines 29 unresolved extreme observations as missing while preserving vendor-based returns. The supplied net holdings have 82 retail and 46 institutional forecast dates lacking a complete 500-return window after quarantine. Do not compute a seemingly complete VaR by deleting dates, filling zero, or using future returns. Member 3 should report these gaps or restore verified observations with evidence. The enhanced strategy requires its own coverage check with current signed holdings.

Sources: SGX weekly reports; Yahoo chart responses; State Street official ES3 NAV/distributions; official code-change announcements and source-quality evidence recorded with URLs/checksums. AI assistance: ChatGPT assisted with collection, code, auditing and report drafting. Team members remain responsible for interpretation and final verification.

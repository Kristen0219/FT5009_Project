"""Fixed ex-ante trend confirmation; preserve Member 1's ten slots and engine."""
import numpy as np
import pandas as pd

LOOKBACK = 126  # approximately six months; fixed for the lecture-aligned SMA rule


def filter_institutional(flows, prices, calendar, lookback=LOOKBACK):
    """Use 126 consecutive aligned closes ending STRICTLY before release date.

    Reject by replacing the quote key, rather than deleting a row: the original
    engine still sees ten slots per side, leaves rejected allocations in cash,
    and exits rejected existing holdings normally (subject to frozen positions).
    No changes to the price panel, borrow flags or baseline execution engine.
    """
    tri = prices.pivot(index='date', columns='security_id', values='total_return_index').reindex(calendar)
    average = tri.rolling(lookback, min_periods=lookback).mean()
    complete = tri.notna().rolling(lookback, min_periods=lookback).sum().eq(lookback)
    trend_gap = tri / average - 1
    filtered = flows.copy()
    audit = []
    for idx, row in flows[flows.investor.eq('institutional')].iterrows():
        pos = calendar.searchsorted(row.publication_date, side='left') - 1
        signal_date = calendar[pos] if pos >= 0 else pd.NaT
        sid = row.security_id
        value = np.nan
        reason = 'missing_history'
        accepted = False
        if pos >= lookback-1 and sid in tri and complete.loc[signal_date, sid]:
            value = trend_gap.loc[signal_date, sid]
            accepted = bool(value > 0 if row.side == 'buy' else value < 0)
            reason = 'trend_confirmed' if accepted else 'trend_not_confirmed'
        if not accepted:
            filtered.loc[idx, 'security_id'] = 'FILTERED::' + sid
        audit.append(dict(report_id=row.report_id, publication_date=row.publication_date,
                          security_id=sid, side=row.side, rank=row['rank'],
                          information_date=signal_date, price_to_sma126_minus_one=value,
                          accepted=accepted, reason=reason))
    return filtered, pd.DataFrame(audit)

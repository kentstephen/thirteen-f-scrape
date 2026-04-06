WITH agg AS (
    SELECT
        h.cik,
        COALESCE(f.display_name, h.entity_name) as fund,
        h.filing_date, h.report_date,
        h.issuer, h.cusip, h.put_call,
        SUM(h.value_x1000) as value_x1000,
        SUM(h.shares) as shares
    FROM holdings h
    LEFT JOIN funds f ON h.cik = f.cik
    GROUP BY h.cik, f.display_name, h.entity_name, h.filing_date, h.report_date, h.issuer, h.cusip, h.put_call
),
ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY cik, cusip, COALESCE(put_call, '')
            ORDER BY report_date DESC
        ) as rn
    FROM agg
),
current_q AS (SELECT * FROM ranked WHERE rn = 1),
prior_q AS (SELECT * FROM ranked WHERE rn = 2)
SELECT
    c.cik,
    c.fund,
    c.report_date as current_quarter,
    p.report_date as prior_quarter,
    c.issuer,
    c.cusip,
    c.put_call,
    c.shares as current_shares,
    p.shares as prior_shares,
    c.value_x1000 / 1000 as current_value_m,
    COALESCE(p.value_x1000, 0) / 1000 as prior_value_m,
    (c.value_x1000 - COALESCE(p.value_x1000, 0)) / 1000 as value_change_m,
    c.shares - COALESCE(p.shares, 0) as shares_change,
    CASE
        WHEN p.shares IS NULL THEN 'NEW'
        WHEN c.shares > p.shares THEN 'INCREASED'
        WHEN c.shares < p.shares THEN 'DECREASED'
        ELSE 'UNCHANGED'
    END as change_type,
    CASE
        WHEN p.shares IS NULL OR p.shares = 0 THEN NULL
        ELSE ROUND(100.0 * (c.shares - p.shares) / p.shares, 1)
    END as pct_change
FROM current_q c
LEFT JOIN prior_q p
    ON c.cik = p.cik
    AND c.cusip = p.cusip
    AND COALESCE(c.put_call, '') = COALESCE(p.put_call, '')
ORDER BY ABS(c.value_x1000 - COALESCE(p.value_x1000, 0)) DESC

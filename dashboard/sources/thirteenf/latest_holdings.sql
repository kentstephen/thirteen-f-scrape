WITH latest AS (
    SELECT cik, MAX(report_date) as max_report_date
    FROM holdings
    GROUP BY cik
)
SELECT
    COALESCE(f.display_name, h.entity_name) as fund,
    h.cik,
    h.issuer,
    h.cusip,
    h.report_date,
    SUM(h.value_x1000) / 1000 as value_m,
    SUM(h.shares) as shares,
    h.put_call
FROM holdings h
JOIN latest l ON h.cik = l.cik AND h.report_date = l.max_report_date
LEFT JOIN funds f ON h.cik = f.cik
GROUP BY f.display_name, h.entity_name, h.cik, h.issuer, h.cusip, h.report_date, h.put_call
ORDER BY fund, value_m DESC

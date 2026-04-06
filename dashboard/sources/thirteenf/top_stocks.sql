WITH latest AS (
    SELECT cik, MAX(report_date) as max_report_date
    FROM holdings
    GROUP BY cik
)
SELECT
    h.issuer,
    h.cusip,
    COUNT(DISTINCT h.cik) as num_funds,
    SUM(h.value_x1000) / 1000 as total_value_m,
    SUM(h.shares) as total_shares
FROM holdings h
JOIN latest l ON h.cik = l.cik AND h.report_date = l.max_report_date
WHERE h.put_call IS NULL
GROUP BY h.issuer, h.cusip
HAVING num_funds >= 2
ORDER BY total_value_m DESC

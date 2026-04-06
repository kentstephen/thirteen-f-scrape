SELECT
    COALESCE(f.display_name, h.entity_name) as fund,
    h.cik,
    h.filing_date,
    h.report_date,
    COUNT(DISTINCT h.cusip) as positions,
    SUM(h.value_x1000) / 1000 as total_value_m
FROM holdings h
LEFT JOIN funds f ON h.cik = f.cik
GROUP BY f.display_name, h.entity_name, h.cik, h.filing_date, h.report_date
ORDER BY fund, h.filing_date DESC

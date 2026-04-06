SELECT DISTINCT COALESCE(f.display_name, h.entity_name) as fund, h.cik
FROM holdings h
LEFT JOIN funds f ON h.cik = f.cik
ORDER BY fund

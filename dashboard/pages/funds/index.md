---
title: All Funds
---

```sql funds
SELECT
    fund,
    cik,
    report_date,
    total_value_m,
    positions
FROM thirteenf.fund_summary
ORDER BY fund, report_date DESC
```

```sql fund_trend
SELECT fund, report_date, total_value_m
FROM thirteenf.fund_summary
ORDER BY fund, report_date
```

## AUM Over Time

<LineChart
    data={fund_trend}
    x=report_date
    y=total_value_m
    yFmt="$#,##0M"
    series=fund
    title="Portfolio Value by Quarter"
/>

## All Funds (Latest Filing)

```sql latest_per_fund
SELECT fund, cik, report_date, total_value_m, positions
FROM thirteenf.fund_summary
WHERE (fund, report_date) IN (
    SELECT fund, MAX(report_date) FROM thirteenf.fund_summary GROUP BY fund
)
ORDER BY total_value_m DESC
```

<DataTable data={latest_per_fund} search=true link=cik>
    <Column id=fund title="Fund" />
    <Column id=total_value_m title="AUM ($M)" fmt="$#,##0" />
    <Column id=positions title="Positions" />
    <Column id=report_date title="Quarter" />
</DataTable>

## Quarterly History

<DataTable data={funds} search=true rows=20>
    <Column id=fund title="Fund" />
    <Column id=report_date title="Quarter" />
    <Column id=total_value_m title="AUM ($M)" fmt="$#,##0" />
    <Column id=positions title="Positions" />
</DataTable>

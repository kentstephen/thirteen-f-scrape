---
title: Fund Detail
---

```sql fund_info
SELECT fund, cik, report_date, total_value_m, positions
FROM thirteenf.fund_summary
WHERE cik = '${params.cik}'
ORDER BY report_date DESC
```

# {fund_info[0].fund}

```sql holdings
SELECT issuer, cusip, value_m, shares, put_call
FROM thirteenf.latest_holdings
WHERE cik = '${params.cik}'
ORDER BY value_m DESC
```

```sql changes
SELECT issuer, change_type, current_value_m, prior_value_m, value_change_m,
       current_shares, prior_shares, shares_change, pct_change
FROM thirteenf.position_changes
WHERE cik = '${params.cik}'
  AND change_type != 'UNCHANGED'
ORDER BY ABS(value_change_m) DESC
```

```sql aum_trend
SELECT report_date, total_value_m, positions
FROM thirteenf.fund_summary
WHERE cik = '${params.cik}'
ORDER BY report_date
```

<BigValue data={fund_info} value=total_value_m title="Latest AUM ($M)" fmt="$#,##0" />
<BigValue data={fund_info} value=positions title="Positions" />
<BigValue data={fund_info} value=report_date title="Latest Quarter" />

## AUM Over Time

<LineChart
    data={aum_trend}
    x=report_date
    y=total_value_m
    yFmt="$#,##0M"
    title="Portfolio Value"
/>

## Top Holdings

<BarChart
    data={holdings.slice(0, 15)}
    x=issuer
    y=value_m
    yFmt="$#,##0M"
    title="Top 15 Holdings by Value"
    swapXY=true
    sort=false
/>

<DataTable data={holdings} search=true rows=25>
    <Column id=issuer title="Stock" />
    <Column id=cusip title="CUSIP" />
    <Column id=value_m title="Value ($M)" fmt="$#,##0" />
    <Column id=shares title="Shares" fmt="#,##0" />
    <Column id=put_call title="Put/Call" />
</DataTable>

## Position Changes (vs Prior Quarter)

```sql new_pos
SELECT * FROM ${changes} WHERE change_type = 'NEW'
```

```sql increased
SELECT * FROM ${changes} WHERE change_type = 'INCREASED'
```

```sql decreased
SELECT * FROM ${changes} WHERE change_type = 'DECREASED'
```

### New Positions
<DataTable data={new_pos} rows=15>
    <Column id=issuer title="Stock" />
    <Column id=current_value_m title="Value ($M)" fmt="$#,##0" />
    <Column id=current_shares title="Shares" fmt="#,##0" />
</DataTable>

### Increased
<DataTable data={increased} rows=15>
    <Column id=issuer title="Stock" />
    <Column id=pct_change title="% Change" fmt="+#,##0.0%" />
    <Column id=value_change_m title="Value Change ($M)" fmt="$+#,##0" />
    <Column id=current_value_m title="Current ($M)" fmt="$#,##0" />
</DataTable>

### Decreased
<DataTable data={decreased} rows=15>
    <Column id=issuer title="Stock" />
    <Column id=pct_change title="% Change" fmt="#,##0.0%" />
    <Column id=value_change_m title="Value Change ($M)" fmt="$#,##0" />
    <Column id=current_value_m title="Current ($M)" fmt="$#,##0" />
</DataTable>

[Back to All Funds](/funds)

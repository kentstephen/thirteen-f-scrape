---
title: 13F Filings Dashboard
---

Large institutional investment managers with over $100M in Assets Under Management (AUM) are required to file <a href="https://www.sec.gov/divisions/investment/13ffaq" target="_blank">Form 13F</a> with the SEC each quarter, disclosing their equity holdings. This dashboard tracks those filings to show what the biggest hedge funds are buying and selling.

```sql quarters
SELECT DISTINCT report_date
FROM thirteenf.fund_summary
ORDER BY report_date DESC
```

```sql fund_count
SELECT COUNT(DISTINCT fund) as n
FROM thirteenf.fund_summary
```

<Dropdown data={quarters} name=quarter value=report_date title="Filing Quarter">
    <DropdownOption value="%" valueLabel="All Quarters" />
</Dropdown>

<Dropdown name=show_count title="Show Top N Funds (by AUM)">
    <DropdownOption value="10" valueLabel="Top 10" />
    <DropdownOption value="25" valueLabel="Top 25" default />
    <DropdownOption value="50" valueLabel="All Funds" />
</Dropdown>

```sql fund_aum
SELECT
    s.fund,
    s.report_date,
    s.total_value_m,
    s.positions
FROM thirteenf.fund_summary s
WHERE s.report_date = (SELECT MAX(report_date) FROM thirteenf.fund_summary WHERE fund = s.fund)
AND CAST(s.report_date AS VARCHAR) like '${inputs.quarter.value}'
ORDER BY s.total_value_m DESC
LIMIT ${inputs.show_count.value}
```

## Portfolio Size by Fund

<BarChart
    data={fund_aum}
    x=fund
    y=total_value_m
    yFmt="#,##0"
    xAxisTitle="Fund"
    yAxisTitle="AUM ($M)"
    title="Assets Under Management ($M)"
    swapXY=true
    sort=false
/>

<DataTable data={fund_aum} search=true rows=20>
    <Column id=fund title="Fund" />
    <Column id=total_value_m title="AUM ($M)" fmt="#,##0" />
    <Column id=positions title="Positions" />
    <Column id=report_date title="Quarter" />
</DataTable>

---

## New Positions This Quarter

Stocks that funds opened brand new positions in.

```sql new_positions
SELECT fund, issuer, current_value_m, current_shares
FROM thirteenf.position_changes pc
WHERE change_type = 'NEW'
AND fund IN (SELECT fund FROM ${fund_aum})
ORDER BY current_value_m DESC
LIMIT 20
```

<BarChart
    data={new_positions}
    x=issuer
    y=current_value_m
    yFmt="#,##0"
    series=fund
    title="Biggest New Buys ($M)"
    swapXY=true
    sort=false
    xAxisTitle="Stock"
    yAxisTitle="Position Value ($M)"
/>

<DataTable data={new_positions} search=true>
    <Column id=fund title="Fund" />
    <Column id=issuer title="Stock" />
    <Column id=current_value_m title="Value ($M)" fmt="#,##0" />
    <Column id=current_shares title="Shares" fmt="#,##0" />
</DataTable>

---

## Biggest Increases

Existing positions where funds added significantly more shares.

```sql biggest_increases
SELECT fund, issuer, pct_change, value_change_m, current_value_m, current_quarter, prior_quarter
FROM thirteenf.position_changes
WHERE change_type = 'INCREASED' AND pct_change IS NOT NULL
AND fund IN (SELECT fund FROM ${fund_aum})
ORDER BY value_change_m DESC
LIMIT 20
```

<BarChart
    data={biggest_increases}
    x=issuer
    y=value_change_m
    yFmt="#,##0"
    series=fund
    title="Biggest Position Increases ($M Added)"
    swapXY=true
    sort=false
    xAxisTitle="Stock"
    yAxisTitle="Value Increase ($M)"
    colorPalette={['#4ade80','#22c55e','#16a34a','#15803d','#166534','#14532d','#86efac','#bbf7d0','#dcfce7','#a3e635']}
/>

<DataTable data={biggest_increases} search=true>
    <Column id=fund title="Fund" />
    <Column id=issuer title="Stock" />
    <Column id=pct_change title="% Change" fmt="+0.0" />
    <Column id=value_change_m title="Value Added ($M)" fmt="+#,##0" />
    <Column id=current_value_m title="Current Value ($M)" fmt="#,##0" />
    <Column id=prior_quarter title="Prior Quarter" />
    <Column id=current_quarter title="Current Quarter" />
</DataTable>

---

## Biggest Decreases

Positions where funds are selling — trimming or reducing their holdings.

```sql biggest_decreases
SELECT fund, issuer, pct_change, value_change_m * -1 as value_sold_m, current_value_m, current_quarter, prior_quarter
FROM thirteenf.position_changes
WHERE change_type = 'DECREASED'
AND fund IN (SELECT fund FROM ${fund_aum})
ORDER BY value_change_m ASC
LIMIT 20
```

<BarChart
    data={biggest_decreases}
    x=issuer
    y=value_sold_m
    yFmt="#,##0"
    series=fund
    title="Biggest Position Decreases ($M Sold)"
    swapXY=true
    sort=false
    xAxisTitle="Stock"
    yAxisTitle="Value Sold ($M)"
    colorPalette={['#f87171','#ef4444','#dc2626','#b91c1c','#991b1b','#7f1d1d','#fca5a5','#fecaca','#fee2e2','#fb923c']}
/>

<DataTable data={biggest_decreases} search=true>
    <Column id=fund title="Fund" />
    <Column id=issuer title="Stock" />
    <Column id=pct_change title="% Change" fmt="0.0" />
    <Column id=value_sold_m title="Value Sold ($M)" fmt="#,##0" />
    <Column id=current_value_m title="Remaining Value ($M)" fmt="#,##0" />
    <Column id=prior_quarter title="Prior Quarter" />
    <Column id=current_quarter title="Current Quarter" />
</DataTable>

---

## Most Widely Held Stocks

Stocks held by multiple tracked funds — signals broad institutional conviction.

```sql popular
SELECT issuer, num_funds, total_value_m
FROM thirteenf.top_stocks
ORDER BY num_funds DESC, total_value_m DESC
LIMIT 25
```

<BarChart
    data={popular}
    x=issuer
    y=total_value_m
    yFmt="#,##0"
    title="Stocks Held by 2+ Funds — Combined Position Value ($M)"
    swapXY=true
    sort=false
    xAxisTitle="Stock"
    yAxisTitle="Combined Value ($M)"
/>

<DataTable data={popular} search=true>
    <Column id=issuer title="Stock" />
    <Column id=num_funds title="# Funds Holding" />
    <Column id=total_value_m title="Total Value ($M)" fmt="#,##0" />
</DataTable>

---

<a href="/funds">View All Funds</a>

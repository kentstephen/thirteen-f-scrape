# 13F Scrape

SEC EDGAR 13F filings scraper and dashboard. Tracks what major hedge funds are buying and selling each quarter.

## Stack

- **Data**: Python async fetcher pulling from SEC EDGAR API
- **Storage**: DuckDB
- **Dashboard**: Evidence (BI as code) — static site deployed to GitHub Pages
- **Orchestration**: Dagster (coming soon)

## What It Does

- Fetches 13F filings for 50 large institutional managers
- Computes quarter-over-quarter position changes (new buys, increases, decreases)
- Landing page with AUM chart, biggest moves, and most widely held stocks
- Per-fund detail pages with holdings and position change breakdowns

## Running Locally

```bash
# Fetch data from SEC EDGAR
uv run thirteenf-fetch

# Run the dashboard
cd dashboard
npm install
npm run sources
npm run dev
```

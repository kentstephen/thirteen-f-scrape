# Research Plan: 13F Scraper + Dashboard

## Overview

Build an automated pipeline that scrapes SEC EDGAR for 13F-HR filings, processes the data, and presents it in a dashboard showing what major hedge funds are buying/selling.

## Architecture

```
EDGAR (SEC) --> Scraper --> Dagster Pipeline --> DuckDB --> Evidence Dashboard
```

## Research Areas

### 1. EDGAR Data Access — How to get 13F data

- [ ] **SEC EDGAR full-text search API** — EDGAR has an EFTS API at `efts.sec.gov/LATEST/search-index?q=...` and a company search API. Investigate rate limits and data format.
- [ ] **EDGAR bulk data** — SEC provides bulk filing archives at `www.sec.gov/Archives/edgar/full-index/`. 13F-HR filings are XML. May be simpler than scraping HTML.
- [ ] **EDGAR XBRL/structured data** — 13F filings use a specific XML schema (`informationTable.xml`). This is structured data, not HTML — may not need a traditional scraper at all.
- [ ] **SEC API headers** — SEC requires a `User-Agent` header with contact info. No API key needed but must comply with fair use (10 req/sec max).
- [ ] **Existing libraries** — Check: `sec-edgar-downloader` (Python), `edgartools`, `sec-api.io` (paid), `python-sec`.

**Key question**: Can we avoid scraping entirely and just parse the structured XML/JSON feeds?

### 2. Scraping Approach — If scraping is needed

- [ ] **`requests` + `BeautifulSoup`** — Simplest. Good if we just need to fetch and parse a few pages. Low overhead.
- [ ] **`Scrapy`** — Full framework with rate limiting, retries, caching built in. Overkill if EDGAR data is already structured, but great if we need to crawl many pages.
- [ ] **`httpx` + `lxml`** — Async HTTP + fast XML parsing. Good middle ground for structured XML data.
- [ ] **Non-Python options** — Unlikely needed, but note: EDGAR data is XML/JSON so any language works. Python has the best ecosystem for the rest of the stack.

**Recommendation to research first**: Start with the structured EDGAR data approach (XML feeds + `requests`). Only reach for Scrapy if we need to crawl/discover filings dynamically.

### 3. Dagster — Orchestration

- [ ] Dagster assets model — define each step as a software-defined asset
- [ ] Scheduling — daily/quarterly checks for new filings (13F filed within 45 days of quarter end)
- [ ] Dagster + DuckDB integration — `dagster-duckdb` package exists
- [ ] Dagster sensors — trigger pipeline when new filings appear on EDGAR
- [ ] Local dev with `dagster dev` vs eventual deployment

### 4. DuckDB — Storage & Analytics

- [ ] Schema design — funds, filings, holdings, position changes
- [ ] DuckDB's native CSV/Parquet/JSON ingestion
- [ ] Incremental loading — append new filings, compute position diffs
- [ ] Querying patterns — quarter-over-quarter position changes, new positions, exits

### 5. Evidence — Dashboard

- [ ] Evidence + DuckDB connector (`evidence-connector-duckdb`)
- [ ] Key dashboard pages:
  - Top funds overview (AUM, filing date)
  - Fund detail page (all holdings, changes)
  - Stock detail page (which funds hold it, who's buying/selling)
  - New positions / exits across all tracked funds
  - Sector/industry breakdown
- [ ] Evidence deployment options (static site, Vercel, self-host)

## Phased Implementation Plan

### Phase 1: Data Access Spike
- Research EDGAR data formats and access patterns
- Write a minimal script to fetch one 13F filing and parse it
- Validate data quality and completeness

### Phase 2: Core Pipeline
- Define DuckDB schema
- Build Dagster assets: fetch → parse → load
- Backfill historical data (start with top 20 funds)

### Phase 3: Dashboard
- Set up Evidence project
- Build core dashboard pages
- Connect to DuckDB

### Phase 4: Automation
- Dagster scheduling and sensors
- Incremental updates
- Alerting on notable position changes

## Target Funds (Initial)

These are some of the most-watched 13F filers:

| Fund | CIK | Why |
|------|-----|-----|
| Berkshire Hathaway | 0001067983 | Buffett |
| Bridgewater Associates | 0001350694 | Dalio |
| Renaissance Technologies | 0001037389 | Medallion adjacency |
| Citadel Advisors | 0001423053 | Griffin |
| Pershing Square | 0001336528 | Ackman |
| Appaloosa Management | 0001656456 | Tepper |
| Tiger Global | 0001167483 | Tech-focused |
| Scion Asset Management | 0001649339 | Burry |
| Duquesne Family Office | 0001536411 | Druckenmiller |
| Third Point | 0001040273 | Loeb |

## Open Questions

1. How far back should we go for historical data? (affects initial load time)
2. Do we want to track 13F-HR/A (amendments) or just original filings?
3. Should we enrich with stock price data (e.g., from Yahoo Finance) to calculate position values at current prices vs filing date?
4. How to handle funds that reorganize or change CIK numbers?

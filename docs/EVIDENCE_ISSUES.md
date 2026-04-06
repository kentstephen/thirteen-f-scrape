# Evidence BI — Performance Issues & Lessons Learned

Date: 2026-04-06

## The Two-Input Limit

Evidence dev mode becomes unacceptably slow when a page has more than two `${inputs.*}` references in its query chain. With one or two inputs (e.g., a quarter Dropdown + a LIMIT Dropdown), pages load instantly. Adding a third input — regardless of type (Slider, Dropdown, ButtonGroup) — causes multi-second page loads.

### What was tested

All tests run on localhost with Evidence v40.1.8, DuckDB connector v2.0.1, 50 funds, ~220K total source rows.

| Inputs on page | Components | Result |
|---|---|---|
| 1 (quarter dropdown) | Original committed state | **Fast** — instant loads |
| 2 (quarter + show_count dropdown) | Added LIMIT dropdown | **Fast** — instant loads |
| 3 (quarter + min_aum slider + max_aum slider) | Dual AUM range sliders | **Slow** — 5+ second loads |
| 3 (quarter + show_count + skip dropdowns) | LIMIT + OFFSET dropdowns | **Slow** — 5+ second loads |
| 2 (quarter + ButtonGroup with 4 tiers) | Hardcoded AUM tier buttons | **Slow** — appeared slow, not fully isolated |

### What was ruled out

- **Data volume**: Reduced sources from 220K rows to ~10K rows (capped to top 25 per fund). Still slow with 3 inputs. Fast with 2 inputs even at 220K rows.
- **Stale cache**: Nuked `.evidence/` directory entirely and rebuilt. No improvement.
- **DuckDB WASM pre-bundling**: Tried `EVIDENCE_DISABLE_INCLUDE=true` to defer WASM loading. No improvement.
- **Port collision**: Dagster was on port 3000 (Evidence default). Moved Evidence to 3001. This was a real issue but not the cause of the slowness.
- **basePath config**: Added/removed `deployment.basePath` — no effect on dev speed.

### Root cause hypothesis

Evidence's reactive query system re-evaluates all queries on the page when any input changes. Each query that references `${inputs.*}` triggers downstream queries that reference `${query_name}`. With 3+ inputs, the combinatorial re-evaluation appears to grow non-linearly. The quarter dropdown was already triggering re-eval of `fund_aum` + 4 downstream queries (new_positions, biggest_increases, biggest_decreases, popular). Adding more inputs to the same query chain multiplies the re-evaluation cost.

This is likely an Evidence framework issue, not a DuckDB or data issue.

## DuckDB WASM File Size

The DuckDB WASM binaries are 33-38MB each. Two are bundled in the static build:

- `duckdb-mvp.wasm` — 38MB
- `duckdb-eh.wasm` — 33MB

Total static build: **147MB** (94MB in `_app/` alone).

### Hosting implications

| Platform | File size limit | Works? |
|---|---|---|
| GitHub Pages | 100MB per file, 1GB total repo | **Yes** — WASM files are under 100MB |
| Cloudflare Pages | 25MB per file | **No** — WASM files exceed limit |
| Vercel | 50MB serverless function limit | **Untested** — static assets may be fine |

Cloudflare Pages was attempted and is a dead end due to the 25MB file limit. GitHub Pages is the viable static hosting option.

## Source Data Volume

With 50 funds, the source queries produce:

- `latest_holdings`: 93,067 rows (BlackRock alone = 48K positions)
- `position_changes`: 118,901 rows
- `top_stocks`: 7,735 rows
- `fund_summary`: 198 rows
- `fund_list`: 50 rows

Evidence loads ALL source data into the browser as parquet files via DuckDB WASM. The 93K + 119K rows create 2.2MB + 4.3MB parquet files. This did NOT cause the observed slowness (proven by reverting to original 220K rows with 2 inputs = fast), but is worth monitoring.

We tested capping sources to top 25 holdings per fund (93K → 1,156 rows, 119K → 1,214 rows). This is available as an option if needed but was reverted since it wasn't the root cause.

## Port Collision with Dagster

Dagster runs on port 3000 by default. Evidence also defaults to 3000. Running both causes silent conflicts. Dashboard `package.json` should use `--port 3001` to avoid this. Currently the committed dev script still uses the default port — needs to be updated.

## Evidence Cache Corruption

During development, the `.evidence/` directory can get into bad states:

- Deleted source SQL files leave stale parquet artifacts in `.evidence/template/static/data/` and `.evidence/meta/`. Running `npm run sources` does NOT clean these up. Must manually delete the stale directories.
- `.evidence/template/.svelte-kit/` can become non-empty and cause `ENOTEMPTY` errors on build. Fix: `rm -rf dashboard/.evidence/template/.svelte-kit/`
- Nuclear option: `rm -rf dashboard/.evidence/` and re-run `npm run sources` to rebuild from scratch.

## Working Configuration (as of 2026-04-06)

- Evidence v40.1.8 with `@evidence-dev/duckdb` v2.0.1
- Dev: `npx evidence dev --port 3001` from `dashboard/`
- Max 2 `${inputs.*}` references per query chain
- Quarter dropdown + Top N dropdown = fast
- 50 funds, full source data (no row caps)
- Node 25.9.0, Python 3.13

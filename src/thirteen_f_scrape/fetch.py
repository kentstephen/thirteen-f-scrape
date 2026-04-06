"""Fetch 13F filings for all target funds and load into DuckDB."""

import asyncio

from tqdm import tqdm

from .db import filing_exists, fund_has_quarters, get_connection, insert_holdings, sync_fund_names
from .edgar import close, fetch_holdings, get_13f_filings
from .funds import FUNDS


async def _fetch_fund(
    fund_name: str, cik: str, filings_per_fund: int, con, bar: tqdm
) -> tuple[int, list[str]]:
    """Fetch all filings for a single fund."""
    holdings_count = 0
    errors = []

    # Skip if we already have enough data for this CIK
    if fund_has_quarters(con, cik, needed=filings_per_fund):
        tqdm.write(f"  [{fund_name}] already has {filings_per_fund} quarters — skipping")
        bar.update(1)
        return 0, errors

    try:
        filings = await get_13f_filings(cik, limit=filings_per_fund)
    except Exception as e:
        msg = f"[{fund_name}] failed to list filings: {e}"
        tqdm.write(msg)
        errors.append(msg)
        bar.update(1)
        return 0, errors

    for filing in filings:
        label = f"[{fund_name}] {filing['filing_date']}"
        if filing_exists(con, filing["accession_number"]):
            continue
        try:
            holdings = await fetch_holdings(cik, filing["accession_number"])
            insert_holdings(con, filing, holdings)
            holdings_count += len(holdings)
            tqdm.write(f"  {label} — {len(holdings)} holdings loaded")
        except Exception as e:
            msg = f"  {label} — ERROR: {e}"
            tqdm.write(msg)
            errors.append(msg)

    bar.update(1)
    return holdings_count, errors


async def _fetch_all_async(filings_per_fund: int = 4, db_path: str = "thirteen_f.duckdb"):
    con = get_connection(db_path)

    # Sync our friendly names into the DB
    sync_fund_names(con, FUNDS)

    bar = tqdm(total=len(FUNDS), desc="Funds", unit="fund")
    tasks = [
        _fetch_fund(name, cik, filings_per_fund, con, bar)
        for name, cik in FUNDS.items()
    ]
    results = await asyncio.gather(*tasks)
    bar.close()

    await close()
    con.close()

    total_holdings = sum(r[0] for r in results)
    all_errors = [e for r in results for e in r[1]]
    print(f"\nDone — {total_holdings:,} holdings loaded, {len(all_errors)} errors")
    if all_errors:
        for err in all_errors:
            print(f"  {err}")
    print(f"Saved to {db_path}")


def fetch_all(filings_per_fund: int = 4, db_path: str = "thirteen_f.duckdb"):
    asyncio.run(_fetch_all_async(filings_per_fund, db_path))


if __name__ == "__main__":
    fetch_all()

"""Fetch 13F filings for all target funds and load into DuckDB."""

from .db import filing_exists, get_connection, insert_holdings
from .edgar import fetch_holdings, get_13f_filings
from .funds import FUNDS


def fetch_all(filings_per_fund: int = 4, db_path: str = "thirteen_f.duckdb"):
    """Fetch recent 13F filings for all target funds."""
    con = get_connection(db_path)

    for fund_name, cik in FUNDS.items():
        print(f"\n{'='*60}")
        print(f"{fund_name} (CIK: {cik})")
        print(f"{'='*60}")

        try:
            filings = get_13f_filings(cik, limit=filings_per_fund)
        except Exception as e:
            print(f"  ERROR fetching filing list: {e}")
            continue

        print(f"  Found {len(filings)} recent 13F filings")

        for filing in filings:
            if filing_exists(con, filing["accession_number"]):
                print(f"  {filing['filing_date']} — already loaded, skipping")
                continue

            print(f"  {filing['filing_date']} ({filing['form']}) — fetching...", end="")
            try:
                holdings = fetch_holdings(cik, filing["accession_number"])
                insert_holdings(con, filing, holdings)
                print(f" {len(holdings)} holdings loaded")
            except Exception as e:
                print(f" ERROR: {e}")

    con.close()
    print(f"\nDone. Data saved to {db_path}")


if __name__ == "__main__":
    fetch_all()

"""Discover the top 13F filers by AUM from EDGAR quarterly index."""

import re
import time

from .edgar import HEADERS, _throttled_get, get_13f_filings, find_info_table_url, _parse_info_table


def get_13f_filers_from_index(year: int = 2026, qtr: int = 1) -> list[dict]:
    """Parse the EDGAR quarterly index to find all 13F-HR filers."""
    url = f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{qtr}/company.idx"
    resp = _throttled_get(url, timeout=60)
    lines = resp.text.splitlines()

    filers = []
    for line in lines:
        if "13F-HR" not in line:
            continue
        # Fixed-width format: name(62) type(12) cik(12) date(12) filename
        match = re.match(
            r"(.{62})(13F-HR\S*)\s+(\d+)\s+(\d{4}-\d{2}-\d{2})\s+(.*)", line
        )
        if match:
            name = match.group(1).strip()
            form = match.group(2).strip()
            cik = match.group(3).strip()
            date = match.group(4).strip()
            filename = match.group(5).strip()
            # Skip amendments for discovery — we want original filings
            if form == "13F-HR":
                filers.append({
                    "name": name,
                    "cik": cik,
                    "filing_date": date,
                    "filename": filename,
                })
    return filers


def rank_filers_by_aum(filers: list[dict], top_n: int = 100) -> list[dict]:
    """Fetch the total value from each filer's 13F and rank by AUM.

    This fetches the info table for each filer to get total portfolio value.
    To avoid hammering EDGAR, we sample and estimate.
    """
    print(f"Found {len(filers)} 13F-HR filers, fetching portfolio values...")

    ranked = []
    for i, filer in enumerate(filers):
        if i % 50 == 0 and i > 0:
            print(f"  Processed {i}/{len(filers)}...")

        try:
            # Get filings list to find the info table
            filings = get_13f_filings(filer["cik"], limit=1)
            if not filings:
                continue

            filing = filings[0]
            info_url = find_info_table_url(filer["cik"], filing["accession_number"])
            if not info_url:
                continue

            resp = _throttled_get(info_url, timeout=60)
            holdings = _parse_info_table(resp.text)
            total_value = sum(h["value_x1000"] for h in holdings)

            filer["entity_name"] = filing["entity_name"]
            filer["total_value_x1000"] = total_value
            filer["num_holdings"] = len(holdings)
            ranked.append(filer)

        except Exception as e:
            # Skip filers we can't fetch
            continue

    ranked.sort(key=lambda x: x["total_value_x1000"], reverse=True)
    return ranked[:top_n]


def discover_top_funds(top_n: int = 100) -> dict[str, str]:
    """Discover the top N 13F filers by AUM. Returns {name: cik}."""
    filers = get_13f_filers_from_index(2026, 1)
    # Deduplicate by CIK (some file multiple times)
    seen = set()
    unique = []
    for f in filers:
        if f["cik"] not in seen:
            seen.add(f["cik"])
            unique.append(f)

    ranked = rank_filers_by_aum(unique, top_n)

    print(f"\nTop {len(ranked)} funds by AUM:")
    for i, f in enumerate(ranked):
        val_b = f["total_value_x1000"] / 1_000_000
        print(f"  {i+1:>3}. {f['entity_name']:<50} ${val_b:>10,.1f}B  ({f['num_holdings']} holdings)")

    return {f["entity_name"]: f["cik"] for f in ranked}


if __name__ == "__main__":
    funds = discover_top_funds(100)

    # Output as Python dict for funds.py
    print("\n\n# Paste into funds.py:")
    print("FUNDS: dict[str, str] = {")
    for name, cik in funds.items():
        print(f'    "{name}": "{cik}",')
    print("}")

"""
Spike: Fetch a 13F filing from EDGAR and load holdings into DuckDB.

This validates the end-to-end data pipeline:
  EDGAR JSON API -> informationTable XML -> parsed holdings -> DuckDB
"""

import xml.etree.ElementTree as ET

import duckdb
import httpx

HEADERS = {"User-Agent": "ThirteenFScrape research@example.com"}
SEC_BASE = "https://data.sec.gov"
ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"
NS = {"ns": "http://www.sec.gov/edgar/document/thirteenf/informationtable"}

# Target funds to test with
FUNDS = {
    "Berkshire Hathaway": "0001067983",
    "Scion Asset Management": "0001649339",  # Michael Burry
}


def get_recent_13f_filings(cik: str, limit: int = 3) -> list[dict]:
    """Get recent 13F-HR filings for a given CIK from the submissions API."""
    padded_cik = cik.lstrip("0").zfill(10)
    url = f"{SEC_BASE}/submissions/CIK{padded_cik}.json"
    resp = httpx.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    recent = data["filings"]["recent"]
    filings = []
    for i, form in enumerate(recent["form"]):
        if form in ("13F-HR", "13F-HR/A"):
            filings.append(
                {
                    "cik": cik.lstrip("0"),
                    "entity_name": data["name"],
                    "accession_number": recent["accessionNumber"][i],
                    "filing_date": recent["filingDate"][i],
                    "form": form,
                    "primary_doc": recent["primaryDocument"][i],
                }
            )
            if len(filings) >= limit:
                break
    return filings


def find_info_table_url(cik: str, accession: str) -> str | None:
    """Find the informationTable XML file URL from a filing's index page."""
    cik_num = cik.lstrip("0")
    acc_no_dashes = accession.replace("-", "")
    index_url = f"{ARCHIVES_BASE}/{cik_num}/{acc_no_dashes}/index.json"
    resp = httpx.get(index_url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    for item in data.get("directory", {}).get("item", []):
        name = item.get("name", "").lower()
        # The info table is typically an XML file that isn't the primary_doc.xml
        if name.endswith(".xml") and name != "primary_doc.xml":
            return f"{ARCHIVES_BASE}/{cik_num}/{acc_no_dashes}/{item['name']}"
    return None


def parse_info_table(xml_text: str) -> list[dict]:
    """Parse the 13F informationTable XML into a list of holdings."""
    root = ET.fromstring(xml_text)
    holdings = []
    for entry in root.findall("ns:infoTable", NS):
        holding = {
            "issuer": entry.findtext("ns:nameOfIssuer", namespaces=NS),
            "title_of_class": entry.findtext("ns:titleOfClass", namespaces=NS),
            "cusip": entry.findtext("ns:cusip", namespaces=NS),
            "value_x1000": int(entry.findtext("ns:value", namespaces=NS) or 0),
            "shares": int(
                entry.find("ns:shrsOrPrnAmt/ns:sshPrnamt", NS).text  # type: ignore
            ),
            "share_type": entry.find("ns:shrsOrPrnAmt/ns:sshPrnamtType", NS).text,  # type: ignore
            "put_call": entry.findtext("ns:putCall", namespaces=NS),
            "investment_discretion": entry.findtext(
                "ns:investmentDiscretion", namespaces=NS
            ),
        }
        holdings.append(holding)
    return holdings


def load_to_duckdb(
    con: duckdb.DuckDBPyConnection,
    filing: dict,
    holdings: list[dict],
):
    """Load parsed holdings into DuckDB."""
    for h in holdings:
        con.execute(
            """
            INSERT INTO holdings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                filing["cik"],
                filing["entity_name"],
                filing["accession_number"],
                filing["filing_date"],
                h["issuer"],
                h["title_of_class"],
                h["cusip"],
                h["value_x1000"],
                h["shares"],
                h["share_type"],
                h["put_call"],
            ],
        )


def main():
    con = duckdb.connect("thirteen_f.duckdb")
    con.execute("""
        CREATE TABLE IF NOT EXISTS holdings (
            cik VARCHAR,
            entity_name VARCHAR,
            accession_number VARCHAR,
            filing_date DATE,
            issuer VARCHAR,
            title_of_class VARCHAR,
            cusip VARCHAR,
            value_x1000 BIGINT,
            shares BIGINT,
            share_type VARCHAR,
            put_call VARCHAR
        )
    """)
    # Clear previous runs
    con.execute("DELETE FROM holdings")

    for fund_name, cik in FUNDS.items():
        print(f"\n{'='*60}")
        print(f"Fetching 13F filings for {fund_name} (CIK: {cik})")
        print(f"{'='*60}")

        filings = get_recent_13f_filings(cik, limit=2)
        print(f"Found {len(filings)} recent 13F filings")

        for filing in filings:
            print(f"\n  Filing: {filing['form']} on {filing['filing_date']}")
            print(f"  Accession: {filing['accession_number']}")

            info_url = find_info_table_url(cik, filing["accession_number"])
            if not info_url:
                print("  WARNING: Could not find informationTable XML")
                continue

            print(f"  Fetching: {info_url}")
            resp = httpx.get(info_url, headers=HEADERS, timeout=60)
            resp.raise_for_status()

            holdings = parse_info_table(resp.text)
            print(f"  Parsed {len(holdings)} holdings")

            load_to_duckdb(con, filing, holdings)

    # Print summary
    print(f"\n{'='*60}")
    print("DuckDB Summary")
    print(f"{'='*60}")

    result = con.execute("""
        SELECT entity_name, filing_date, COUNT(*) as num_holdings,
               SUM(value_x1000) / 1000 as total_value_millions
        FROM holdings
        GROUP BY entity_name, filing_date
        ORDER BY entity_name, filing_date DESC
    """).fetchall()

    for row in result:
        print(f"  {row[0]} | {row[1]} | {row[2]} holdings | ${row[3]:,.0f}M")

    # Show top 10 holdings for most recent Berkshire filing
    print(f"\n  Top 10 Holdings (Berkshire, most recent filing):")
    top = con.execute("""
        SELECT issuer, cusip, value_x1000 / 1000 as value_millions, shares
        FROM holdings
        WHERE entity_name LIKE 'BERKSHIRE%'
        ORDER BY filing_date DESC, value_x1000 DESC
        LIMIT 10
    """).fetchall()
    for row in top:
        print(f"    {row[0]:<30} {row[1]}  ${row[2]:>10,.0f}M  {row[3]:>15,} shares")

    con.close()
    print(f"\nData saved to thirteen_f.duckdb")


if __name__ == "__main__":
    main()

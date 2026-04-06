"""SEC EDGAR API client for 13F filings. Async with rate limiting."""

import asyncio
import xml.etree.ElementTree as ET

import httpx

HEADERS = {"User-Agent": "ThirteenFScrape research@example.com"}
SEC_BASE = "https://data.sec.gov"
ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"
NS = {"ns": "http://www.sec.gov/edgar/document/thirteenf/informationtable"}

# SEC fair-use: max 10 req/sec. Semaphore limits concurrency,
# small sleep between requests keeps us under the limit.
MAX_CONCURRENT = 8
REQUEST_DELAY = 0.12  # ~8 req/sec effective

_semaphore: asyncio.Semaphore | None = None
_client: httpx.AsyncClient | None = None


async def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(headers=HEADERS, timeout=60)
    return _client


async def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    return _semaphore


async def _throttled_get(url: str) -> httpx.Response:
    """Rate-limited async GET."""
    sem = await _get_semaphore()
    client = await _get_client()
    async with sem:
        await asyncio.sleep(REQUEST_DELAY)
        resp = await client.get(url)
        resp.raise_for_status()
        return resp


async def get_13f_filings(cik: str, limit: int = 10) -> list[dict]:
    """Get recent 13F-HR filings for a CIK from the submissions API."""
    padded = cik.lstrip("0").zfill(10)
    url = f"{SEC_BASE}/submissions/CIK{padded}.json"
    resp = await _throttled_get(url)
    data = resp.json()

    recent = data["filings"]["recent"]
    filings = []
    for i, form in enumerate(recent["form"]):
        if form in ("13F-HR", "13F-HR/A"):
            filings.append({
                "cik": cik.lstrip("0"),
                "entity_name": data["name"],
                "accession_number": recent["accessionNumber"][i],
                "filing_date": recent["filingDate"][i],
                "report_date": recent.get("reportDate", [None] * len(recent["form"]))[i],
                "form": form,
            })
            if len(filings) >= limit:
                break
    return filings


async def find_info_table_url(cik: str, accession: str) -> str | None:
    """Find the informationTable XML URL from a filing's index."""
    cik_num = cik.lstrip("0")
    acc_no_dashes = accession.replace("-", "")
    index_url = f"{ARCHIVES_BASE}/{cik_num}/{acc_no_dashes}/index.json"
    resp = await _throttled_get(index_url)
    data = resp.json()

    for item in data.get("directory", {}).get("item", []):
        name = item.get("name", "").lower()
        if name.endswith(".xml") and name != "primary_doc.xml":
            return f"{ARCHIVES_BASE}/{cik_num}/{acc_no_dashes}/{item['name']}"
    return None


async def fetch_holdings(cik: str, accession: str) -> list[dict]:
    """Fetch and parse the informationTable XML for a filing."""
    url = await find_info_table_url(cik, accession)
    if not url:
        return []
    resp = await _throttled_get(url)
    return _parse_info_table(resp.text)


async def close():
    """Close the async client."""
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None


def _parse_info_table(xml_text: str) -> list[dict]:
    """Parse 13F informationTable XML into holdings dicts."""
    root = ET.fromstring(xml_text)
    holdings = []
    for entry in root.findall("ns:infoTable", NS):
        shares_el = entry.find("ns:shrsOrPrnAmt/ns:sshPrnamt", NS)
        share_type_el = entry.find("ns:shrsOrPrnAmt/ns:sshPrnamtType", NS)
        holdings.append({
            "issuer": entry.findtext("ns:nameOfIssuer", namespaces=NS),
            "title_of_class": entry.findtext("ns:titleOfClass", namespaces=NS),
            "cusip": entry.findtext("ns:cusip", namespaces=NS),
            "value_x1000": int(entry.findtext("ns:value", namespaces=NS) or 0),
            "shares": int(shares_el.text) if shares_el is not None else 0,
            "share_type": share_type_el.text if share_type_el is not None else None,
            "put_call": entry.findtext("ns:putCall", namespaces=NS),
            "investment_discretion": entry.findtext("ns:investmentDiscretion", namespaces=NS),
        })
    return holdings

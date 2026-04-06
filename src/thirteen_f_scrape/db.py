"""DuckDB schema and loading."""

import duckdb

DB_PATH = "thirteen_f.duckdb"


def get_connection(path: str = DB_PATH) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(path)
    _ensure_schema(con)
    return con


def _ensure_schema(con: duckdb.DuckDBPyConnection):
    # Lookup table: our friendly names keyed by CIK
    con.execute("""
        CREATE TABLE IF NOT EXISTS funds (
            cik VARCHAR PRIMARY KEY,
            display_name VARCHAR NOT NULL,
            category VARCHAR
        )
    """)

    # Raw holdings from EDGAR
    con.execute("""
        CREATE TABLE IF NOT EXISTS holdings (
            cik VARCHAR,
            entity_name VARCHAR,
            accession_number VARCHAR,
            filing_date DATE,
            report_date DATE,
            issuer VARCHAR,
            title_of_class VARCHAR,
            cusip VARCHAR,
            value_x1000 BIGINT,
            shares BIGINT,
            share_type VARCHAR,
            put_call VARCHAR,
            PRIMARY KEY (accession_number, cusip, shares)
        )
    """)

    # Aggregated holdings joined with our fund names
    con.execute("""
        CREATE OR REPLACE VIEW holdings_aggregated AS
        SELECT
            h.cik,
            COALESCE(f.display_name, h.entity_name) as fund,
            h.filing_date,
            h.report_date,
            h.issuer,
            h.cusip,
            SUM(h.value_x1000) as value_x1000,
            SUM(h.shares) as shares,
            h.put_call
        FROM holdings h
        LEFT JOIN funds f ON h.cik = f.cik
        GROUP BY h.cik, f.display_name, h.entity_name, h.filing_date, h.report_date, h.issuer, h.cusip, h.put_call
    """)

    con.execute("""
        CREATE OR REPLACE VIEW position_changes AS
        WITH ranked AS (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY cik, cusip, COALESCE(put_call, '')
                    ORDER BY report_date DESC
                ) as rn
            FROM holdings_aggregated
        ),
        current_q AS (SELECT * FROM ranked WHERE rn = 1),
        prior_q AS (SELECT * FROM ranked WHERE rn = 2)
        SELECT
            c.cik,
            c.fund,
            c.report_date as current_report_date,
            p.report_date as prior_report_date,
            c.issuer,
            c.cusip,
            c.put_call,
            c.shares as current_shares,
            p.shares as prior_shares,
            c.value_x1000 as current_value_x1000,
            p.value_x1000 as prior_value_x1000,
            c.shares - COALESCE(p.shares, 0) as shares_change,
            CASE
                WHEN p.shares IS NULL THEN 'NEW'
                WHEN c.shares > p.shares THEN 'INCREASED'
                WHEN c.shares < p.shares THEN 'DECREASED'
                ELSE 'UNCHANGED'
            END as change_type,
            CASE
                WHEN p.shares IS NULL OR p.shares = 0 THEN NULL
                ELSE ROUND(100.0 * (c.shares - p.shares) / p.shares, 2)
            END as pct_change
        FROM current_q c
        LEFT JOIN prior_q p
            ON c.cik = p.cik
            AND c.cusip = p.cusip
            AND COALESCE(c.put_call, '') = COALESCE(p.put_call, '')
    """)

    con.execute("""
        CREATE OR REPLACE VIEW exited_positions AS
        WITH ranked AS (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY cik, cusip, COALESCE(put_call, '')
                    ORDER BY report_date DESC
                ) as rn
            FROM holdings_aggregated
        ),
        current_q AS (SELECT * FROM ranked WHERE rn = 1),
        prior_q AS (SELECT * FROM ranked WHERE rn = 2)
        SELECT
            p.cik,
            p.fund,
            p.report_date as last_held_date,
            c.report_date as current_report_date,
            p.issuer,
            p.cusip,
            p.put_call,
            p.shares as last_shares,
            p.value_x1000 as last_value_x1000
        FROM prior_q p
        LEFT JOIN current_q c
            ON p.cik = c.cik
            AND p.cusip = c.cusip
            AND COALESCE(p.put_call, '') = COALESCE(c.put_call, '')
        WHERE c.cusip IS NULL
    """)


def sync_fund_names(con: duckdb.DuckDBPyConnection, funds: dict[str, str]):
    """Sync our friendly fund names into the funds table."""
    for display_name, cik in funds.items():
        con.execute(
            "INSERT OR REPLACE INTO funds (cik, display_name) VALUES (?, ?)",
            [cik.lstrip("0"), display_name],
        )


def fund_has_quarters(con: duckdb.DuckDBPyConnection, cik: str, needed: int = 4) -> bool:
    """Check if we already have enough quarters for this fund."""
    result = con.execute(
        "SELECT COUNT(DISTINCT report_date) FROM holdings WHERE cik = ?",
        [cik.lstrip("0")],
    ).fetchone()
    return result is not None and result[0] >= needed


def filing_exists(con: duckdb.DuckDBPyConnection, accession_number: str) -> bool:
    result = con.execute(
        "SELECT 1 FROM holdings WHERE accession_number = ? LIMIT 1",
        [accession_number],
    ).fetchone()
    return result is not None


def insert_holdings(
    con: duckdb.DuckDBPyConnection,
    filing: dict,
    holdings: list[dict],
):
    if not holdings:
        return
    rows = [
        (
            filing["cik"],
            filing["entity_name"],
            filing["accession_number"],
            filing["filing_date"],
            filing.get("report_date"),
            h["issuer"],
            h["title_of_class"],
            h["cusip"],
            h["value_x1000"],
            h["shares"],
            h["share_type"],
            h["put_call"],
        )
        for h in holdings
    ]
    con.executemany(
        "INSERT OR IGNORE INTO holdings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )

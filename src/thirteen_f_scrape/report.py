"""Generate reports from the DuckDB holdings data."""

from .db import get_connection


def summary(db_path: str = "thirteen_f.duckdb"):
    """Print a summary of all loaded funds."""
    con = get_connection(db_path)

    print(f"\n{'='*70}")
    print("Portfolio Summary by Fund")
    print(f"{'='*70}")

    rows = con.execute("""
        SELECT entity_name, filing_date, report_date,
               COUNT(DISTINCT cusip) as positions,
               SUM(value_x1000) / 1000 as total_value_m
        FROM holdings
        GROUP BY entity_name, filing_date, report_date
        ORDER BY entity_name, filing_date DESC
    """).fetchall()

    current_fund = None
    for row in rows:
        if row[0] != current_fund:
            current_fund = row[0]
            print(f"\n  {current_fund}")
        print(f"    {row[1]} (Q ending {row[2]}) — {row[3]} positions, ${row[4]:,.0f}M")

    con.close()


def changes(db_path: str = "thirteen_f.duckdb"):
    """Print notable position changes (new, exited, big moves)."""
    con = get_connection(db_path)

    # New positions
    print(f"\n{'='*70}")
    print("NEW POSITIONS (most recent quarter)")
    print(f"{'='*70}")
    rows = con.execute("""
        SELECT entity_name, issuer, cusip, current_shares, current_value_x1000 / 1000 as value_m
        FROM position_changes
        WHERE change_type = 'NEW'
        ORDER BY current_value_x1000 DESC
        LIMIT 30
    """).fetchall()

    for row in rows:
        print(f"  {row[0]:<35} bought {row[1]:<25} ${row[4]:>10,.0f}M  ({row[3]:>12,} shares)")

    # Exited positions
    print(f"\n{'='*70}")
    print("EXITED POSITIONS")
    print(f"{'='*70}")
    rows = con.execute("""
        SELECT entity_name, issuer, cusip, last_shares, last_value_x1000 / 1000 as value_m
        FROM exited_positions
        ORDER BY last_value_x1000 DESC
        LIMIT 30
    """).fetchall()

    for row in rows:
        print(f"  {row[0]:<35} sold all {row[1]:<25} (was ${row[4]:>10,.0f}M)")

    # Biggest increases
    print(f"\n{'='*70}")
    print("BIGGEST INCREASES (by value)")
    print(f"{'='*70}")
    rows = con.execute("""
        SELECT entity_name, issuer, pct_change, shares_change,
               (current_value_x1000 - COALESCE(prior_value_x1000, 0)) / 1000 as value_change_m
        FROM position_changes
        WHERE change_type = 'INCREASED' AND prior_shares > 0
        ORDER BY current_value_x1000 - COALESCE(prior_value_x1000, 0) DESC
        LIMIT 20
    """).fetchall()

    for row in rows:
        print(f"  {row[0]:<35} {row[1]:<25} +{row[2]:>7.1f}%  (+${row[4]:>10,.0f}M)")

    # Biggest decreases
    print(f"\n{'='*70}")
    print("BIGGEST DECREASES (by value)")
    print(f"{'='*70}")
    rows = con.execute("""
        SELECT entity_name, issuer, pct_change, shares_change,
               (current_value_x1000 - COALESCE(prior_value_x1000, 0)) / 1000 as value_change_m
        FROM position_changes
        WHERE change_type = 'DECREASED'
        ORDER BY current_value_x1000 - COALESCE(prior_value_x1000, 0) ASC
        LIMIT 20
    """).fetchall()

    for row in rows:
        print(f"  {row[0]:<35} {row[1]:<25} {row[2]:>7.1f}%  (${row[4]:>10,.0f}M)")

    con.close()


def _cli():
    summary()
    changes()


if __name__ == "__main__":
    _cli()

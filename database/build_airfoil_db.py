from __future__ import annotations
"""Build the final production airfoil database.

This module orchestrates the full pipeline:
1. geometry import into `profiles.db`
2. usage import into `usage.db`
3. XFOIL polar generation into `polars.db`
4. merge into `airfoil.db`

The staging databases may contain profiles that are later excluded. The final
database keeps only the profiles accepted by geometry and XFOIL validation.
"""

import shutil
import sqlite3

from build_polars_db import build_polars_database
from build_profiles_db import build_profiles_database
from build_usage_db import build_usage_database
from paths import (
    AIRFOIL_DB_PATH,
    DB_DIR,
    ensure_local_dirs,
    resolve_polars_db_path,
    resolve_profiles_db_path,
    resolve_usage_db_path,
)

USAGE_TABLES = [
    "aircraft_usage_rows",
    "airfoil_applications",
    "source_meta",
]
POLARS_TABLES = ["airfoil_polars_xfoil", "airfoil_xfoil_runs"]


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name=?
        """,
        (table_name,),
    )
    return cur.fetchone() is not None


def get_create_table_sql(conn: sqlite3.Connection, table_name: str) -> str | None:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type='table' AND name=?
        """,
        (table_name,),
    )
    row = cur.fetchone()
    return row[0] if row else None


def get_indexes_sql(conn: sqlite3.Connection, table_name: str) -> list[str]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type='index'
          AND tbl_name=?
          AND sql IS NOT NULL
        """,
        (table_name,),
    )
    return [row[0] for row in cur.fetchall() if row[0]]


def copy_table_schema(
    src_conn: sqlite3.Connection,
    dst_conn: sqlite3.Connection,
    table_name: str,
) -> None:
    create_sql = get_create_table_sql(src_conn, table_name)
    if not create_sql:
        raise RuntimeError(f"Schema non trovato per la tabella '{table_name}'.")

    dst_cur = dst_conn.cursor()
    dst_cur.execute(create_sql)

    for idx_sql in get_indexes_sql(src_conn, table_name):
        dst_cur.execute(idx_sql)

    dst_conn.commit()


def get_column_names(conn: sqlite3.Connection, table_name: str) -> list[str]:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cur.fetchall()]


def clear_table(conn: sqlite3.Connection, table_name: str) -> None:
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table_name}")
    conn.commit()


def copy_table_data(
    src_conn: sqlite3.Connection,
    dst_conn: sqlite3.Connection,
    table_name: str,
) -> int:
    columns = get_column_names(src_conn, table_name)
    if not columns:
        raise RuntimeError(f"Nessuna colonna trovata per la tabella '{table_name}'.")

    col_list = ", ".join(columns)
    placeholders = ", ".join(["?"] * len(columns))

    src_cur = src_conn.cursor()
    dst_cur = dst_conn.cursor()

    src_cur.execute(f"SELECT {col_list} FROM {table_name}")
    rows = src_cur.fetchall()

    if rows:
        dst_cur.executemany(
            f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})",
            rows,
        )
        dst_conn.commit()

    return len(rows)


def replace_table_from_source(
    src_conn: sqlite3.Connection,
    dst_conn: sqlite3.Connection,
    table_name: str,
) -> int:
    if not table_exists(src_conn, table_name):
        print(f"[WARN] Tabella non trovata, salto: {table_name}")
        return 0

    if not table_exists(dst_conn, table_name):
        copy_table_schema(src_conn, dst_conn, table_name)
    else:
        clear_table(dst_conn, table_name)

    copied = copy_table_data(src_conn, dst_conn, table_name)
    print(f"[OK] {table_name}: copiate {copied} righe")
    return copied


def run_integrity_check(conn: sqlite3.Connection, label: str) -> None:
    cur = conn.cursor()
    cur.execute("PRAGMA integrity_check")
    result = cur.fetchone()
    status = result[0] if result else "unknown"
    print(f"[CHECK] integrity_check {label}: {status}")


def prune_final_airfoils(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    if table_exists(conn, "airfoil_xfoil_runs"):
        count_sql = """
            SELECT COUNT(*)
            FROM airfoils
            WHERE exclude_from_final = 1
               OR name IN (
                    SELECT airfoil_name
                    FROM airfoil_xfoil_runs
                    WHERE exclude_from_final = 1
               )
        """
        delete_sql = """
            DELETE FROM airfoils
            WHERE exclude_from_final = 1
               OR name IN (
                    SELECT airfoil_name
                    FROM airfoil_xfoil_runs
                    WHERE exclude_from_final = 1
               )
        """
    else:
        count_sql = "SELECT COUNT(*) FROM airfoils WHERE exclude_from_final = 1"
        delete_sql = "DELETE FROM airfoils WHERE exclude_from_final = 1"

    cur.execute(count_sql)
    removed = cur.fetchone()[0]
    cur.execute(delete_sql)
    conn.commit()
    return removed


def prune_orphan_polars(conn: sqlite3.Connection) -> int:
    if not table_exists(conn, "airfoil_polars_xfoil"):
        return 0

    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM airfoil_polars_xfoil
        WHERE airfoil_name NOT IN (SELECT name FROM airfoils)
        """
    )
    removed = cur.rowcount if cur.rowcount is not None else 0
    conn.commit()
    return removed


def merge_databases() -> None:
    """Merge staging databases into the final `airfoil.db` output."""
    ensure_local_dirs()

    profiles_db = resolve_profiles_db_path()
    usage_db = resolve_usage_db_path()
    polars_db = resolve_polars_db_path()
    merged_db = AIRFOIL_DB_PATH
    DB_DIR.mkdir(parents=True, exist_ok=True)

    print("PROFILES_DB =", profiles_db)
    print("USAGE_DB    =", usage_db)
    print("POLARS_DB   =", polars_db)
    print("AIRFOIL_DB  =", merged_db)

    if not profiles_db.exists():
        raise FileNotFoundError(f"DB profili non trovato: {profiles_db}")
    if not usage_db.exists():
        raise FileNotFoundError(
            "DB usage non trovato. Attesi uno di questi path:\n"
            f" - {usage_db}\n"
            f" - {usage_db.with_suffix('')}"
        )
    if not polars_db.exists():
        raise FileNotFoundError(f"DB polars non trovato: {polars_db}")

    if merged_db.exists():
        merged_db.unlink()

    shutil.copy2(profiles_db, merged_db)
    print(f"[OK] Copiato DB base profili in: {merged_db}")

    profiles_conn = sqlite3.connect(profiles_db)
    usage_conn = sqlite3.connect(usage_db)
    polars_conn = sqlite3.connect(polars_db)
    merged_conn = sqlite3.connect(merged_db)

    try:
        run_integrity_check(profiles_conn, "profiles")
        run_integrity_check(usage_conn, "usage")
        run_integrity_check(polars_conn, "polars")
        run_integrity_check(merged_conn, "merged-initial")

        total_usage_rows = 0
        for table_name in USAGE_TABLES:
            total_usage_rows += replace_table_from_source(usage_conn, merged_conn, table_name)

        total_polar_rows = 0
        for table_name in POLARS_TABLES:
            total_polar_rows += replace_table_from_source(polars_conn, merged_conn, table_name)

        removed_airfoils = prune_final_airfoils(merged_conn)
        removed_polars = prune_orphan_polars(merged_conn)

        run_integrity_check(merged_conn, "merged-final")

        cur = merged_conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cur.fetchall()]

        print("\n===== MERGE COMPLETATO =====")
        print("DB finale:", merged_db)
        print("Tabelle presenti:")
        for table_name in tables:
            print(" -", table_name)

        print("\nConteggi principali:")
        for table_name in [
            "airfoils",
            "airfoil_polars_xfoil",
            "airfoil_applications",
            "aircraft_usage_rows",
        ]:
            if table_exists(merged_conn, table_name):
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                print(f" - {table_name}: {cur.fetchone()[0]}")

        print(f"\nRighe usage copiate: {total_usage_rows}")
        print(f"Righe polars copiate: {total_polar_rows}")
        print(f"Profili esclusi dal DB finale: {removed_airfoils}")
        print(f"Polari rimosse per profili esclusi: {removed_polars}")

    finally:
        profiles_conn.close()
        usage_conn.close()
        polars_conn.close()
        merged_conn.close()


def build_airfoil_database(
    force_redownload_profiles: bool = False,
    reset_profiles: bool = True,
    reset_usage: bool = True,
    reset_polars: bool = True,
) -> None:
    """Run the complete database build pipeline end to end."""
    print("[STEP 1/4] Building profiles.db")
    build_profiles_database(
        force_redownload=force_redownload_profiles,
        reset_db=reset_profiles,
    )

    print("\n[STEP 2/4] Building usage.db")
    build_usage_database(reset_db=reset_usage)

    print("\n[STEP 3/4] Building polars.db")
    build_polars_database(reset_db=reset_polars)

    print("\n[STEP 4/4] Merging into airfoil.db")
    merge_databases()


if __name__ == "__main__":
    build_airfoil_database()

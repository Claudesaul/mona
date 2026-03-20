"""Database connection functions for LightSpeed, Level, OOS, Salesforce, and Snowflake."""

import os
import pyodbc
import psycopg2
import psycopg2.extras
from simple_salesforce import Salesforce
from dotenv import load_dotenv

# Load .env from project root (parent of backend/)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"), override=True)


def get_lightspeed_connection():
    """Get a read-only connection to the LightSpeed SQL Server database (order data)."""
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    if not username or not password:
        raise ValueError("DB_USERNAME and DB_PASSWORD must be set in .env")

    conn_str = (
        "DRIVER={SQL Server};"
        "SERVER=10.216.207.32;"
        "DATABASE=LightSpeed;"
        f"UID={username};"
        f"PWD={password};"
        "Connection Timeout=30;"
        "ApplicationIntent=ReadOnly;"
    )
    return pyodbc.connect(conn_str, timeout=30)


def get_level_connection():
    """Get a read-only connection to the Level SQL Server database (inventory/warehouse data)."""
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    if not username or not password:
        raise ValueError("DB_USERNAME and DB_PASSWORD must be set in .env")

    conn_str = (
        "DRIVER={SQL Server};"
        "SERVER=10.216.207.32;"
        "DATABASE=Level;"
        f"UID={username};"
        f"PWD={password};"
        "Connection Timeout=30;"
        "ApplicationIntent=ReadOnly;"
    )
    return pyodbc.connect(conn_str, timeout=30)


def get_oos_connection():
    """Get a connection to the PostgreSQL OOS database (out-of-stock tracking)."""
    host = os.getenv("PG_HOST", "10.7.6.146")
    port = os.getenv("PG_PORT", "5432")
    database = os.getenv("PG_DATABASE", "oos")
    username = os.getenv("PG_USERNAME")
    password = os.getenv("PG_PASSWORD")
    if not username or not password:
        raise ValueError("PG_USERNAME and PG_PASSWORD must be set in .env")

    return psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=username,
        password=password,
        connect_timeout=30,
        options="-c statement_timeout=60000",  # 60 second query timeout
    )


def execute_sql_server_query(connection_func, query: str) -> list[dict]:
    """Execute a query against a SQL Server database and return results as list of dicts.

    Args:
        connection_func: Function that returns a pyodbc connection (get_lightspeed_connection or get_level_connection).
        query: SQL query to execute. Will be prefixed with SET LOCK_TIMEOUT for safety.

    Returns:
        List of dicts with column names as keys.
    """
    conn = None
    cursor = None
    try:
        conn = connection_func()
        cursor = conn.cursor()

        # Set lock timeout and execute
        safe_query = f"SET LOCK_TIMEOUT 5000;\n{query}"
        cursor.execute(safe_query)

        # If no result set (e.g. SET statements), return empty
        if cursor.description is None:
            return []

        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]

    except pyodbc.Error as e:
        raise RuntimeError(f"SQL Server query error: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Database error: {str(e)}") from e
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def execute_postgres_query(query: str) -> list[dict]:
    """Execute a query against the PostgreSQL OOS database and return results as list of dicts.

    Args:
        query: SQL query to execute.

    Returns:
        List of dicts with column names as keys.
    """
    conn = None
    cursor = None
    try:
        conn = get_oos_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query)

        if cursor.description is None:
            return []

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    except psycopg2.Error as e:
        raise RuntimeError(f"PostgreSQL query error: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Database error: {str(e)}") from e
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def _get_salesforce_client() -> Salesforce:
    """Get an authenticated Salesforce client."""
    username = os.getenv("SF_USERNAME")
    password = os.getenv("SF_PASSWORD")
    token = os.getenv("SF_SECURITY_TOKEN", "")
    if not username or not password:
        raise ValueError("SF_USERNAME and SF_PASSWORD must be set in .env")
    return Salesforce(username=username, password=password, security_token=token)


def execute_salesforce_query(soql_query: str) -> list[dict]:
    """Execute a SOQL query against Salesforce and return results as list of dicts."""
    try:
        sf = _get_salesforce_client()
        result = sf.query_all(soql_query)
        records = result.get("records", [])
        cleaned = []
        for record in records:
            row = {}
            for key, value in record.items():
                if key == "attributes":
                    continue
                if isinstance(value, dict) and "attributes" in value:
                    for k, v in value.items():
                        if k != "attributes":
                            row[f"{key}.{k}"] = v
                else:
                    row[key] = value
            cleaned.append(row)
        return cleaned
    except Exception as e:
        raise RuntimeError(f"Salesforce query error: {str(e)}") from e


def get_snowflake_connection():
    """Get a connection to the Snowflake SEED data warehouse."""
    username = os.getenv("Snowflake_USERNAME")
    password = os.getenv("Snowflake_PASSWORD")
    if not username or not password:
        raise ValueError("Snowflake_USERNAME and Snowflake_PASSWORD must be set in .env")

    conn_str = (
        "DRIVER={SnowflakeDSIIDriver};"
        "SERVER=kfc56636.us-east-1.snowflakecomputing.com;"
        "DATABASE=PRD_SEED_DW_VIEW_SHARE_V1;"
        "WAREHOUSE=PRD_SEED_OPERATOR_WH;"
        "SCHEMA=PUBLIC;"
        f"UID={username};"
        f"PWD={password};"
    )
    return pyodbc.connect(conn_str, timeout=60)


def execute_snowflake_query(query: str) -> list[dict]:
    """Execute a query against the Snowflake SEED data warehouse."""
    conn = None
    cursor = None
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        # Set statement timeout to 60 seconds
        cursor.execute("ALTER SESSION SET STATEMENT_TIMEOUT_IN_SECONDS = 60")
        cursor.execute(query)

        if cursor.description is None:
            return []

        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]

    except pyodbc.Error as e:
        raise RuntimeError(f"Snowflake query error: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Snowflake error: {str(e)}") from e
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass

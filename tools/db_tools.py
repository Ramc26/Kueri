# tools/db_tools.py

import os
import asyncpg
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------
# Utility: Get DB URL from .env
# ---------------------------------------------------------------------
def _get_db_url(db_key: str) -> str:
    db_url = os.getenv(db_key)
    if not db_url:
        raise ValueError(f"Database key '{db_key}' not found in environment variables.")
    return db_url


# ---------------------------------------------------------------------
# Tool 1: Run arbitrary SQL query
# ---------------------------------------------------------------------
async def run_sql_query(db_key: str, query: str):
    """
    Executes a SQL query on the database defined by the given db_key in .env.
    """
    try:
        db_url = _get_db_url(db_key)
        conn = await asyncpg.connect(db_url)
        try:
            logger.info("Executing query on {}", db_key)
            results = await conn.fetch(query)
            return {"status": "success", "rows": [dict(r) for r in results]}
        finally:
            await conn.close()
    except Exception as e:
        logger.error("SQL execution failed: {}", e)
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------
# Tool 2: List tables in the database
# ---------------------------------------------------------------------
async def list_tables(db_key: str):
    """
    Lists all table names in the specified database.
    """
    try:
        db_url = _get_db_url(db_key)
        conn = await asyncpg.connect(db_url)
        try:
            logger.info("Listing tables for {}", db_key)
            query = """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_type = 'BASE TABLE'
                AND table_schema NOT IN ('pg_catalog', 'information_schema')
                ORDER BY table_schema, table_name;
            """
            rows = await conn.fetch(query)
            tables = [{"schema": r["table_schema"], "table_name": r["table_name"]} for r in rows]
            return {"status": "success", "tables": tables}
        finally:
            await conn.close()
    except Exception as e:
        logger.error("Failed to list tables: {}", e)
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------
# Tool 3: Get table schema (columns)
# ---------------------------------------------------------------------
async def get_table_schema(db_key: str, table_name: str):
    """
    Fetches column names and data types for a specific table.
    """
    try:
        db_url = _get_db_url(db_key)
        conn = await asyncpg.connect(db_url)
        try:
            logger.info("Fetching schema for {}.{}", db_key, table_name)
            query = """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = $1
                ORDER BY ordinal_position;
            """
            rows = await conn.fetch(query, table_name)
            columns = [
                {"column_name": r["column_name"], "data_type": r["data_type"], "is_nullable": r["is_nullable"]}
                for r in rows
            ]
            return {"status": "success", "columns": columns}
        finally:
            await conn.close()
    except Exception as e:
        logger.error("Failed to fetch schema: {}", e)
        return {"status": "error", "message": str(e)}

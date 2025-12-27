# tools/db_tools.py

import os
import json
import asyncpg
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------
# Utility: Load database config from JSON
# ---------------------------------------------------------------------
def _load_db_config(db_key: str) -> dict:
    """Load database configuration from JSON file"""
    # Try to find the database config file
    databases_dir = Path("databases")
    
    # First try exact match
    db_file = databases_dir / f"{db_key}.json"
    if not db_file.exists():
        # Try to find by db_key in metadata
        for config_file in databases_dir.glob("*.json"):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
                    if config.get("metadata", {}).get("db_key") == db_key:
                        db_file = config_file
                        break
            except:
                continue
    
    if not db_file.exists():
        raise ValueError(f"Database config file not found for '{db_key}'. Expected: {databases_dir}/{db_key}.json")
    
    with open(db_file, "r") as f:
        return json.load(f)

# ---------------------------------------------------------------------
# Utility: Build connection string from config
# ---------------------------------------------------------------------
def _build_db_url(config: dict) -> str:
    """Build database connection URL from config"""
    db_config = config.get("config", {})
    db_type = db_config.get("type", "postgresql").lower()
    
    if db_type == "postgresql":
        host = db_config.get("host", "localhost")
        port = db_config.get("port", 5432)
        database = db_config.get("database", "")
        user = db_config.get("user", "")
        password = db_config.get("password", "")
        ssl = db_config.get("ssl", False)
        
        # Support environment variable substitution for password
        if password and password.startswith("${") and password.endswith("}"):
            env_var = password[2:-1]
            password = os.getenv(env_var, "")
            if not password:
                logger.warning(f"Environment variable '{env_var}' not found, using empty password")
        
        # Build PostgreSQL connection string
        if password:
            url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        else:
            url = f"postgresql://{user}@{host}:{port}/{database}"
        
        if ssl:
            url += "?sslmode=require"
        
        return url
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


# ---------------------------------------------------------------------
# Tool 1: Run arbitrary SQL query
# ---------------------------------------------------------------------
async def run_sql_query(db_key: str, query: str):
    """
    Executes a SQL query on the database defined by the given db_key.
    Database credentials are loaded from databases/{db_key}.json
    """
    try:
        db_config = _load_db_config(db_key)
        db_url = _build_db_url(db_config)
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
    Database credentials are loaded from databases/{db_key}.json
    """
    try:
        db_config = _load_db_config(db_key)
        db_url = _build_db_url(db_config)
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
    Database credentials are loaded from databases/{db_key}.json
    """
    try:
        db_config = _load_db_config(db_key)
        db_url = _build_db_url(db_config)
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

from tools.db_tools import run_sql_query, list_tables, get_table_schema

def register_db_tools(mcp):
    mcp.tool()(run_sql_query)
    mcp.tool()(list_tables)
    mcp.tool()(get_table_schema)

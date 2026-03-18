"""Tool definitions for Claude API tool_use."""

TOOLS = [
    {
        "name": "query_snowflake",
        "description": (
            "Query the Snowflake SEED data warehouse. THIS IS THE PRIMARY DATABASE for: "
            "revenue, sales dollars, prices, fulfillment, delivery, spoilage value, margins. "
            "Contains 47M+ sales rows, 31M+ fulfillment rows, 20M+ micro market transactions. "
            "Fact tables join to dimension tables via KEY columns (LOCATIONKEY, ITEMKEY, ROUTEKEY). "
            "Date keys are YYYYMMDD integers (e.g., 20260318). Use Snowflake SQL. Always LIMIT results."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": (
                        "Snowflake SQL SELECT query. Always join fact→dim for readable names. "
                        "Always filter by date key. Always include LIMIT 500 or less."
                    ),
                },
            },
            "required": ["sql_query"],
        },
    },
    {
        "name": "query_lightspeed",
        "description": (
            "Query LightSpeed SQL Server for order and pick status. "
            "Shows what was ordered, when, pick/delivery status. "
            "PRIMARY TABLE: dbo.ItemView (~4.7M rows). "
            "WARNING: No price/cost/revenue columns — use Snowflake for financial questions. "
            "Use T-SQL. Always include TOP and filter by orderDate."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": "T-SQL SELECT with TOP 500 or less. Filter by orderDate.",
                },
            },
            "required": ["sql_query"],
        },
    },
    {
        "name": "query_level",
        "description": (
            "Query Level SQL Server for warehouse inventory, par levels, purchase orders, and vendors. "
            "Key view: dbo.AreaItemParView (current stock and pars). Use T-SQL. Always include TOP."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": "T-SQL SELECT with TOP 500 or less.",
                },
            },
            "required": ["sql_query"],
        },
    },
    {
        "name": "query_oos",
        "description": (
            "Query PostgreSQL OOS database for fill rates, out-of-stock data, and product activity. "
            "oos_details_by_date: coil-level stock readings (12M rows, MUST filter by date). "
            "product_activity: rolling 14-day movement data (NO date column, do NOT filter by date). "
            "v_daily_oos: daily OOS % by location. Use PostgreSQL syntax. Always LIMIT."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": (
                        "PostgreSQL SELECT with LIMIT 500 or less. "
                        "MUST filter oos_details_by_date by date. "
                        "product_activity has NO date column — query it without date filters."
                    ),
                },
            },
            "required": ["sql_query"],
        },
    },
    {
        "name": "query_salesforce",
        "description": (
            "Query Salesforce CRM for customer accounts, contacts, tasks, events, cases, opportunities. "
            "Use SOQL syntax. Always include LIMIT 200 or less."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "soql_query": {
                    "type": "string",
                    "description": "SOQL SELECT with LIMIT 200 or less.",
                },
            },
            "required": ["soql_query"],
        },
    },
]

"""Tool definitions for Claude API tool_use."""

TOOLS = [
    {
        "name": "query_snowflake",
        "description": (
            "Query the Snowflake SEED data warehouse. THIS IS THE PRIMARY DATABASE for: "
            "revenue, sales dollars, prices, fulfillment, delivery, spoilage value, margins. "
            "Contains 47M+ sales rows, 31M+ fulfillment rows, 20M+ micro market transactions. "
            "Fact tables join to dimension tables via KEY columns (LOCATIONKEY, ITEMKEY, ROUTEKEY). "
            "IMPORTANT: Date keys are serial integers, NOT YYYYMMDD. "
            "Use VISITDATETIME/SALEDATETIME timestamps for date filtering. "
            "Use Snowflake SQL. Always LIMIT results."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": (
                        "Snowflake SQL SELECT query. Always join fact→dim for readable names. "
                        "Filter dates with VISITDATETIME >= '2026-03-19' (timestamp), NOT datekey. "
                        "Always include LIMIT 500 or less."
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
            "PRIMARY TABLE: dbo.ItemView (~4.8M rows). "
            "Also: dbo.OrderTotals, dbo.RouteTotals for aggregates. "
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
            "Query Level SQL Server for warehouse inventory, par levels, purchase orders, "
            "receiving history, and vendors. "
            "Key views: dbo.AreaItemParView (current stock/pars), dbo.QohByArea (QOH by area), "
            "dbo.ReceiptView (receiving with costs), dbo.PoiView (PO items with velocity). "
            "Use T-SQL. Always include TOP."
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
            "oos_details_by_date: coil-level stock readings (12.5M rows, MUST filter by date). "
            "product_activity: rolling 14-day movement data (NO date column, do NOT filter by date). "
            "v_daily_oos: today's fill rate and OOS count by location. "
            "v_daily_oos_details: today's OOS coils with demand/days-on-hand metrics. "
            "v_weekly_oos: weekly OOS trends. v_future_daily_oos: predicted shorts. "
            "IMPORTANT: View columns use Title Case with spaces — use double quotes. "
            "Use PostgreSQL syntax. Always LIMIT."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": (
                        "PostgreSQL SELECT with LIMIT 500 or less. "
                        "MUST filter oos_details_by_date by date. "
                        "product_activity has NO date column — query without date filters. "
                        "View columns need double quotes: SELECT \"Location\", \"Fill\" FROM v_daily_oos"
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
            "2,092 accounts (customers + prospects), 44K cases (mostly equipment installs), "
            "12K tasks, 4K opportunities. Use SOQL syntax. Always include LIMIT 200 or less."
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
    {
        "name": "search_sharepoint",
        "description": (
            "Search shared drive files (SharePoint synced via OneDrive). "
            "Covers 3 document libraries: Business Intelligence, Customer Operations, Standards & Process. "
            "~9,100 files: Excel reports (xlsx/xlsm), Word docs (docx), PDFs, CSVs, PowerPoints. "
            "Use for: finding reports, pricing files, templates, process docs, merchandising sheets. "
            "Returns file metadata with download links. Does NOT read file contents."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "search_term": {
                    "type": "string",
                    "description": (
                        "Filename or keyword to search for (case-insensitive, partial match). "
                        "Examples: 'OCS report', 'pricing', 'spoilage', 'weekly sales'"
                    ),
                },
                "folder": {
                    "type": "string",
                    "description": (
                        "Optional folder path to narrow search (relative to root). "
                        "Examples: 'Business Intelligence - Documents/Reporting/Daily', "
                        "'Customer Operations - Documents'. Empty = search all libraries."
                    ),
                },
                "file_type": {
                    "type": "string",
                    "description": "Optional file extension filter: 'xlsx', 'pdf', 'docx', 'csv'. Empty = all types.",
                },
                "modified_after": {
                    "type": "string",
                    "description": "Optional date filter (YYYY-MM-DD). Only files modified on or after this date.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Max files to return (default 20, max 50).",
                },
            },
            "required": ["search_term"],
        },
    },
]

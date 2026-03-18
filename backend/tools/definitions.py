"""Tool definitions for Claude API tool_use format.

These tools allow Claude to query Monumental Markets business databases
to answer user questions about orders, inventory, and out-of-stock data.
"""

TOOLS = [
    {
        "name": "query_lightspeed",
        "description": (
            "Query the LightSpeed SQL Server database for order and transaction data. "
            "This database contains item-level order data from Monumental Markets vending "
            "and micro-market operations. The primary view is dbo.ItemView with ~4.7M rows. "
            "Use T-SQL syntax. Always include TOP to limit results. "
            "Common filters: orderDate, locDescription, rteDescription, statusId."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": (
                        "A read-only T-SQL SELECT query to run against the LightSpeed database. "
                        "Must be a SELECT statement. Include TOP 500 or less to limit results. "
                        "Example: SELECT TOP 100 locDescription, product, quantity, orderDate "
                        "FROM dbo.ItemView WHERE orderDate >= '2026-03-01'"
                    ),
                },
            },
            "required": ["sql_query"],
        },
    },
    {
        "name": "query_level",
        "description": (
            "Query the Level SQL Server database for inventory, warehouse, and purchasing data. "
            "Contains par levels (dbo.AreaItemParView), purchase orders, items, and vendors. "
            "Use T-SQL syntax. Always include TOP to limit results."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": (
                        "A read-only T-SQL SELECT query to run against the Level database. "
                        "Must be a SELECT statement. Include TOP 500 or less to limit results. "
                        "Example: SELECT TOP 100 AreaName, ItemName, ParLevel "
                        "FROM dbo.AreaItemParView WHERE CategoryName = 'Snacks'"
                    ),
                },
            },
            "required": ["sql_query"],
        },
    },
    {
        "name": "query_oos",
        "description": (
            "Query the PostgreSQL OOS (Out-of-Stock) database for stock level and product activity data. "
            "Main table: oos_details_by_date (~12M rows) - ALWAYS filter by date. "
            "Also: product_activity (sales/shrinkage), v_daily_oos (daily OOS %), "
            "v_weekly_oos (weekly OOS %), v_daily_oos_details (coil-level OOS). "
            "Use PostgreSQL syntax. Always include LIMIT to cap results. "
            "CRITICAL: Always include a WHERE date filter on large tables."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": (
                        "A read-only PostgreSQL SELECT query to run against the OOS database. "
                        "Must be a SELECT statement. Include LIMIT 500 or less. "
                        "ALWAYS include a date filter on oos_details_by_date and product_activity. "
                        "Example: SELECT location, oos_percentage, date FROM v_daily_oos "
                        "WHERE date = '2026-03-17' ORDER BY oos_percentage DESC LIMIT 20"
                    ),
                },
            },
            "required": ["sql_query"],
        },
    },
    {
        "name": "query_salesforce",
        "description": (
            "Query Salesforce CRM data using SOQL (Salesforce Object Query Language). "
            "Contains customer accounts (2K+), contacts (5K+), tasks (12K+), events (19K+), "
            "cases (43K+), opportunities (3K+), and leads (13K+). "
            "Use SOQL syntax (similar to SQL). Key objects: Account, Contact, Task, Event, Case, Opportunity, Lead. "
            "Common Account fields: Name, Type, BillingCity, BillingState, Industry, OwnerId, CreatedDate. "
            "Common Task fields: Subject, Status, Priority, ActivityDate, Description, AccountId, OwnerId. "
            "Common Contact fields: Name, Email, Phone, AccountId, Title. "
            "Use relationships: e.g. Account.Name from Contact, or What.Name from Task."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "soql_query": {
                    "type": "string",
                    "description": (
                        "A read-only SOQL SELECT query to run against Salesforce. "
                        "Must be a SELECT statement. Include LIMIT 200 or less. "
                        "Example: SELECT Name, Type, BillingCity FROM Account WHERE Type = 'Customer' LIMIT 50"
                    ),
                },
            },
            "required": ["soql_query"],
        },
    },
]

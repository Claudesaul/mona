"""Core chat handler for Mona AI assistant.

Uses Anthropic Claude API with tool_use to query Monumental Markets business
databases and provide analytical insights.
"""

import json
import os
import re
import logging
from datetime import datetime
from typing import AsyncGenerator

import anthropic
from dotenv import load_dotenv

from db.connections import (
    execute_sql_server_query,
    execute_postgres_query,
    execute_snowflake_query,
    get_lightspeed_connection,
    get_level_connection,
    execute_salesforce_query,
)
from db.schemas import get_schema_description
from tools.definitions import TOOLS
import cache

logger = logging.getLogger(__name__)

# Load .env from project root
from pathlib import Path as _Path
load_dotenv(_Path(__file__).resolve().parent.parent / ".env", override=True)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096
MAX_TOOL_ROUNDS = 10  # Prevent infinite tool loops

SYSTEM_PROMPT = f"""You are Mona, a data assistant for Monumental Markets (vending/micro-market operator, D.C. area). You query databases to answer business questions. Today is {datetime.now().strftime('%Y-%m-%d')} ({datetime.now().strftime('%A')}).

## Which database to use

| Question about | Database | Key table |
|---|---|---|
| Revenue, sales $, prices, margins | **Snowflake** | RECOGNIZESALESREVENUEFACT_V |
| How much money a location made | **Snowflake** | RECOGNIZESALESREVENUEFACT_V |
| Sales by coil position | **Snowflake** | SALESBYCOILFACT_V |
| Micro market individual transactions | **Snowflake** | MICROMARKETSALESFACT_V |
| Order fulfillment, what was delivered | **Snowflake** | ORDERTOFULFILLMENTVENDINGMARKETFACT_V |
| Order/pick status, what was ordered | **LightSpeed** | dbo.ItemView |
| Pick efficiency, route performance | **LightSpeed** | dbo.RouteTotals, dbo.OrderTotals |
| Fill rate, OOS % | **OOS** | v_daily_oos, v_daily_oos_details |
| Spoilage, shrinkage, sell-through | **OOS** | product_activity |
| OOS trends over weeks | **OOS** | v_weekly_oos, v_weekly_oos_pivot |
| Predicted stock shortages | **OOS** | v_future_daily_oos |
| Warehouse inventory, par levels | **Level** | dbo.AreaItemParView, dbo.QohByArea |
| Purchase orders, receiving, vendors | **Level** | dbo.PurchaseOrder, dbo.ReceiptView, dbo.Vendor |
| Warehouse item velocity/days supply | **Level** | dbo.PoiView |
| Customer accounts, contacts, tasks | **Salesforce** | Account, Contact, Task |
| Equipment installs/removals | **Salesforce** | Case |
| Sales pipeline | **Salesforce** | Opportunity |

## Critical rules

- **LightSpeed has NO price/revenue columns.** Never use it for "how much money" questions. Use Snowflake.
- **product_activity has NO date column.** It's a rolling 14-day snapshot. Query it without date filters.
- **Snowflake date keys are SERIAL INTEGERS (days since 1899-12-31), NOT YYYYMMDD.** Use VISITDATETIME/SALEDATETIME timestamps for filtering.
- **Snowflake fact tables need dimension joins** for readable names:
  - `JOIN DIMLOCATION_V dl ON f.LOCATIONKEY = dl.LOCATIONKEY` → get location NAME
  - `JOIN DIMITEM_V di ON f.ITEMKEY = di.ITEMKEY` → get item NAME, CATEGORY
  - `JOIN DIMROUTE_V dr ON f.ROUTEKEY = dr.ROUTEKEY` → get route NAME
- **OOS view columns use Title Case with spaces** — must double-quote: `SELECT "Location", "Fill" FROM v_daily_oos`
- Always add row limits: TOP 500 (SQL Server), LIMIT 500 (PostgreSQL/Snowflake), LIMIT 200 (Salesforce).
- Always date-filter large tables: oos_details_by_date, dbo.ItemView, all Snowflake fact tables.
- If a query errors, fix and retry silently. Don't explain the error.
- For multi-database questions, query each database separately then combine the results in your response.

## Common calculations

- **Revenue**: `SUM(ACTUALSALESEXTENDEDTOTALREVENUE)` from Snowflake
- **Gross margin**: `SUM(ALLOCATEDSALESEXTENDEDGROSSMARGIN)` from Snowflake
- **Sell-through %**: `100.0 * SUM(sold_qty) / NULLIF(SUM(added_qty), 0)` from product_activity
- **Fill rate**: `"Fill"` from v_daily_oos (0-1 scale, multiply by 100 for %)
- **OOS coils**: `"OOS"` from v_daily_oos (count of out-of-stock coils)
- **Spoilage cost**: `SUM(spoiled_cost)` from product_activity
- **Demand per day**: `"Demand/Day"` from v_daily_oos_details
- **Days on hand**: `"DaysOnHand"` from v_daily_oos_details

## Example queries

**Snowflake — Total revenue last week by location (top 10):**
```sql
SELECT dl.NAME AS location, ROUND(SUM(f.ACTUALSALESEXTENDEDTOTALREVENUE), 2) AS revenue
FROM RECOGNIZESALESREVENUEFACT_V f
JOIN DIMLOCATION_V dl ON f.LOCATIONKEY = dl.LOCATIONKEY
WHERE f.VISITDATETIME >= DATEADD(day, -7, CURRENT_DATE)
  AND f.VISITDATETIME < CURRENT_DATE
GROUP BY dl.NAME
ORDER BY revenue DESC
LIMIT 10
```

**Snowflake — Revenue and margin by item category this month:**
```sql
SELECT di.CATEGORY, ROUND(SUM(f.ACTUALSALESEXTENDEDTOTALREVENUE), 2) AS revenue,
       ROUND(SUM(f.ALLOCATEDSALESEXTENDEDGROSSMARGIN), 2) AS margin
FROM RECOGNIZESALESREVENUEFACT_V f
JOIN DIMITEM_V di ON f.ITEMKEY = di.ITEMKEY
WHERE f.VISITDATETIME >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY di.CATEGORY
ORDER BY revenue DESC
LIMIT 20
```

**LightSpeed — Today's order status summary:**
```sql
SELECT statusId,
  CASE statusId WHEN 1 THEN 'Queried' WHEN 2 THEN 'Queued' WHEN 3 THEN 'Picking'
    WHEN 4 THEN 'Picked' WHEN 5 THEN 'Printed' WHEN 6 THEN 'Filtered' WHEN 7 THEN 'Staged' END AS status,
  COUNT(DISTINCT id) AS orders, SUM(quantity) AS total_items
FROM dbo.ItemView
WHERE orderDate >= CAST(GETDATE() AS DATE)
GROUP BY statusId
```

**OOS — Locations with worst fill rate today:**
```sql
SELECT "Location", "Route", "Fill", "OOS"
FROM v_daily_oos
ORDER BY "Fill" ASC
LIMIT 20
```

**OOS — Top spoilage items (rolling 14 days, no date filter):**
```sql
SELECT item, item_category, location, spoiled_qty, spoiled_cost
FROM product_activity
WHERE spoiled_qty > 0
ORDER BY spoiled_cost DESC
LIMIT 20
```

**Level — Low stock items (below reorder point):**
```sql
SELECT TOP 20 itemName, itemCode, currentQty, FillTo, ReorderPoint, vendorName
FROM dbo.AreaItemParView
WHERE itemActive = 1 AND currentQty < ReorderPoint AND ReorderPoint > 0
ORDER BY (ReorderPoint - currentQty) DESC
```

**Salesforce — Open tasks by account:**
```sql
SELECT Account.Name, Subject, Status, ActivityDate
FROM Task
WHERE IsClosed = false
ORDER BY ActivityDate ASC
LIMIT 50
```

## Business glossary

When the user says → use this:

| Term | Means | Database | Column/Table |
|---|---|---|---|
| revenue, sales, money made | Total revenue | Snowflake | `SUM(ACTUALSALESEXTENDEDTOTALREVENUE)` from RECOGNIZESALESREVENUEFACT_V |
| margin, profit, gross margin | Gross margin | Snowflake | `SUM(ALLOCATEDSALESEXTENDEDGROSSMARGIN)` |
| cost, product cost | Extended cost | Snowflake | `SUM(EXTENDEDCOST)` |
| fill rate, fill % | % of coils stocked | OOS | `"Fill"` from v_daily_oos (0-1 scale) |
| OOS, out of stock | Empty coil positions | OOS | `"OOS"` from v_daily_oos (count) |
| spoilage, spoils, expired | Spoiled product | OOS | `spoiled_qty`, `spoiled_cost` from product_activity |
| shrinkage, shrink | Inventory loss | OOS | `shrink_qty`, `shrink_cost` from product_activity |
| sell-through | % of stocked items sold | OOS | `100.0 * sold_qty / NULLIF(added_qty, 0)` from product_activity |
| demand, velocity | Daily sales rate | OOS | `"Demand/Day"` from v_daily_oos_details |
| days on hand, DOH | Days until depleted | OOS | `"DaysOnHand"` from v_daily_oos_details |
| predicted shorts, will run out | Forecasted OOS | OOS | `"shorts"` from v_future_daily_oos |
| par, par level | Target stock level | Multiple | Snowflake: `PAR`, Level: `FillTo`, OOS: `par`/`"Par"` |
| inventory, stock, on hand | Current qty | Level | `currentQty` from AreaItemParView or `QOH` from QohByArea |
| warehouse inventory | Warehouse stock | Level | `dbo.AreaItemParView` or `dbo.QohByArea` |
| orders, what was ordered | Order line items | LightSpeed | `dbo.ItemView` filtered by orderDate |
| picks, picking | Warehouse picks | LightSpeed | `dbo.ItemView` statusId + SecondsToPick |
| route performance | Route efficiency | LightSpeed | `dbo.RouteTotals` |
| purchase orders, POs | Vendor orders | Level | `dbo.PurchaseOrder` + `dbo.PoiView` |
| receiving, received | What came in | Level | `dbo.ReceiptView` |
| vendor, supplier | Vendor info | Level | `dbo.Vendor` |
| accounts, customers | CRM accounts | Salesforce | `Account` |
| cases, installs | Equipment installs | Salesforce | `Case` |
| pipeline, opportunities | Sales pipeline | Salesforce | `Opportunity` |
| location, site, market | A vending/market site | Snowflake | `DIMLOCATION_V.NAME` |
| route, driver | Delivery route | Snowflake | `DIMROUTE_V.NAME` |
| item, product, SKU | A product | Snowflake | `DIMITEM_V.NAME` |
| category | Product category | Snowflake | `DIMITEM_V.CATEGORY` |

**Important context:** Snowflake data syncs from Seed at midnight daily — for "today" questions, data may only be current through yesterday. OOS PostgreSQL data is also refreshed daily by Monumator automation.

## Schemas
{get_schema_description()}

## Response style

- Answer first, explain second. No preambles.
- Never start with "Great question", "Let me", "I'll", or "Sure".
- Use markdown tables for data. Max 8 columns. Round numbers to 2 decimals.
- No emoji in headers. No "Key Takeaways" sections unless asked.
- Be concise. If the answer is a number, lead with the number.
"""


def _sanitize_query(sql_query: str) -> str:
    """Validate that a query is read-only and block write operations."""
    query_upper = sql_query.strip().upper()

    # Ensure it starts with SELECT (or WITH for CTEs)
    if not query_upper.startswith("SELECT") and not query_upper.startswith("WITH"):
        raise ValueError("Only SELECT queries (or WITH/CTE) are allowed.")

    # Block write keywords anywhere in the query (catches subqueries, UNION injection, etc.)
    # Uses word-boundary-style matching: keyword must be preceded by whitespace/start
    # and followed by whitespace/end to avoid false positives on column names
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE", "EXEC", "EXECUTE"]
    for keyword in forbidden:
        # Check for keyword as a standalone word (preceded by space/start, followed by space/end)
        if re.search(r'(?<![A-Z])' + keyword + r'(?![A-Z])', query_upper):
            raise ValueError(f"Write operations are not allowed. Blocked keyword: {keyword}")

    return sql_query


def _add_row_limit(sql_query: str, is_postgres: bool = False) -> str:
    """Add row limit to query if not already present."""
    query_upper = sql_query.strip().upper()

    if is_postgres:
        if "LIMIT" not in query_upper:
            sql_query = sql_query.rstrip().rstrip(";") + " LIMIT 500;"
    else:
        # T-SQL: check for TOP
        if "TOP " not in query_upper:
            # Insert TOP 500 after first SELECT
            sql_query = re.sub(
                r"(?i)(SELECT\s+)(DISTINCT\s+)?",
                lambda m: f"{m.group(1)}{m.group(2) or ''}TOP 500 ",
                sql_query,
                count=1,
            )

    return sql_query


def _execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool call and return the result as a string."""

    # Salesforce uses SOQL, not SQL
    if tool_name == "query_salesforce":
        soql_query = tool_input.get("soql_query", "")
        if not soql_query.strip().upper().startswith("SELECT"):
            return json.dumps({"error": "Only SELECT queries are allowed."})

        # Check cache
        cached = cache.get(tool_name, soql_query)
        if cached:
            return cached

        try:
            results = execute_salesforce_query(soql_query)
            result_str = json.dumps(
                {"row_count": len(results), "data": results},
                default=str,
                ensure_ascii=False,
            )
            cache.put(tool_name, soql_query, result_str)
            return result_str
        except Exception as e:
            logger.exception("Salesforce query error")
            return json.dumps({"error": f"Salesforce error: {str(e)}"})

    sql_query = tool_input.get("sql_query", "")

    try:
        sql_query = _sanitize_query(sql_query)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    # Check cache before executing
    cached = cache.get(tool_name, sql_query)
    if cached:
        return cached

    try:
        if tool_name == "query_lightspeed":
            sql_query = _add_row_limit(sql_query, is_postgres=False)
            results = execute_sql_server_query(get_lightspeed_connection, sql_query)
        elif tool_name == "query_level":
            sql_query = _add_row_limit(sql_query, is_postgres=False)
            results = execute_sql_server_query(get_level_connection, sql_query)
        elif tool_name == "query_oos":
            sql_query = _add_row_limit(sql_query, is_postgres=True)
            results = execute_postgres_query(sql_query)
        elif tool_name == "query_snowflake":
            sql_query = _add_row_limit(sql_query, is_postgres=True)  # Snowflake uses LIMIT like postgres
            results = execute_snowflake_query(sql_query)
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        # Serialize results, handling non-JSON-serializable types
        result_str = json.dumps(
            {"row_count": len(results), "data": results},
            default=str,
            ensure_ascii=False,
        )
        cache.put(tool_name, sql_query, result_str)
        return result_str

    except RuntimeError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        logger.exception("Unexpected error executing tool %s", tool_name)
        return json.dumps({"error": f"Unexpected error: {str(e)}"})


class ChatManager:
    """Manages a chat session with conversation history and Claude API interaction."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history: list[dict] = []
        self.client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var
        self.created_at = datetime.now().isoformat()

    def get_history(self) -> list[dict]:
        """Return conversation history for this session."""
        return self.history

    async def send_message(self, user_message: str) -> AsyncGenerator[str, None]:
        """Send a message and yield streaming text chunks.

        Handles the tool_use loop: when Claude requests a tool, execute it,
        feed the result back, and continue until Claude gives a final text response.

        Yields:
            str: Text chunks from Claude's streaming response.
        """
        # Add user message to history
        self.history.append({"role": "user", "content": user_message})

        messages = self._build_messages()
        tool_round = 0

        while tool_round < MAX_TOOL_ROUNDS:
            tool_round += 1

            # Collect the full response to detect tool_use blocks
            response_content = []
            text_chunks = []

            try:
                with self.client.messages.stream(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    system=SYSTEM_PROMPT,
                    messages=messages,
                    tools=TOOLS,
                ) as stream:
                    current_text = ""
                    for event in stream:
                        if event.type == "content_block_start":
                            if event.content_block.type == "text":
                                current_text = ""
                            elif event.content_block.type == "tool_use":
                                # Tool use block starting - we'll handle it after stream completes
                                pass

                        elif event.type == "content_block_delta":
                            if event.delta.type == "text_delta":
                                chunk = event.delta.text
                                current_text += chunk
                                text_chunks.append(chunk)
                                yield chunk

                    # Get the final message to check for tool use
                    final_message = stream.get_final_message()
                    response_content = final_message.content

            except anthropic.APIError as e:
                error_msg = f"\n\nI encountered an API error: {str(e)}. Please try again."
                yield error_msg
                self.history.append({"role": "assistant", "content": error_msg})
                return

            # Check if there are any tool_use blocks
            tool_use_blocks = [block for block in response_content if block.type == "tool_use"]

            if not tool_use_blocks:
                # No tool use - conversation turn is complete
                # Save assistant response to history
                full_text = "".join(text_chunks)
                if full_text:
                    self.history.append({"role": "assistant", "content": full_text})
                self._trim_history()
                return

            # There are tool_use blocks - execute them and continue the loop
            # First, add the assistant's full response (text + tool_use) to messages
            assistant_content = []
            for block in response_content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            messages.append({"role": "assistant", "content": assistant_content})
            # Save tool_use to history so follow-ups have context
            self.history.append({"role": "assistant", "content": assistant_content})

            # Execute each tool and build tool_result messages
            tool_results = []
            for block in tool_use_blocks:
                # Notify user that a query is being executed
                db_label = {
                    "query_lightspeed": "LightSpeed",
                    "query_level": "Level",
                    "query_oos": "OOS (PostgreSQL)",
                    "query_salesforce": "Salesforce",
                    "query_snowflake": "Snowflake",
                }.get(block.name, block.name)

                status_msg = f"\n\n*Querying {db_label} database...*\n\n"
                yield status_msg

                # Execute the tool
                result_str = _execute_tool(block.name, block.input)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_str,
                })

            messages.append({"role": "user", "content": tool_results})
            # Save tool_results to history so follow-ups have context
            self.history.append({"role": "user", "content": tool_results})

            # Clear text_chunks for the next round
            text_chunks = []

        # If we exhausted tool rounds, add a note
        yield "\n\nI've reached the maximum number of database queries for this turn. Please try a more specific question."
        self.history.append({
            "role": "assistant",
            "content": "I've reached the maximum number of database queries for this turn.",
        })
        self._trim_history()

    def _trim_history(self):
        """Trim history to prevent context window overflow.

        Keeps the last 30 messages to maintain conversation context
        while preventing unbounded growth from long sessions.
        """
        max_messages = 30
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]

    def _build_messages(self) -> list[dict]:
        """Build the messages list for the Claude API from conversation history."""
        messages = []
        for entry in self.history:
            messages.append({"role": entry["role"], "content": entry["content"]})
        return messages

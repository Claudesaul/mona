"""Core chat handler for Mona AI assistant.

Uses Anthropic Claude API with tool_use to query Monumental Markets business
databases and provide analytical insights.
"""

import asyncio
import json
import os
import re
import time
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
    search_sharepoint_files,
)
from db.schemas import get_schema_description
from db.query_log import log_conversation, log_message, log_tool_call
from tools.definitions import TOOLS
import cache

logger = logging.getLogger(__name__)

# Load .env from project root
from pathlib import Path as _Path
load_dotenv(_Path(__file__).resolve().parent.parent / ".env", override=True)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096
MAX_TOOL_ROUNDS = 10  # Prevent infinite tool loops

def _build_system_prompt() -> str:
    """Build the system prompt with current date."""
    now = datetime.now()
    return _SYSTEM_PROMPT_TEMPLATE.format(
        today=now.strftime('%Y-%m-%d'),
        weekday=now.strftime('%A'),
        schemas=get_schema_description(),
    )

_SYSTEM_PROMPT_TEMPLATE = """You are Mona, a data analyst for Monumental Markets (vending/micro-market/OCS operator, D.C. area). Today is {today} ({weekday}). Monumental's business week runs Sunday through Saturday. "Last week" means the most recent full Sun–Sat period.

## Decision tree — pick the RIGHT database FIRST

Question about a SPECIFIC account/location? → **Step 1**: Check if it's in OOS first: `SELECT DISTINCT "Location" FROM v_daily_oos WHERE "Location" ILIKE '%name%' LIMIT 3`. If not found, tell the user it's a Delivery account and skip OOS entirely. If found, proceed.
Money/revenue/margin/price → **Snowflake** RECOGNIZESALESREVENUEFACT_V
Fill rate/OOS/spoilage/shrinkage/sell-through → **OOS** (PostgreSQL) — ONLY for Market locations, NOT Delivery
Orders/picks/delivery status → **LightSpeed** dbo.ItemView (NO price data here)
Warehouse stock/par/POs/receiving → **Level** (SQL Server)
Accounts/contacts/tasks/cases/pipeline → **Salesforce** (SOQL)
Files/reports/documents/templates/pricing sheets → **SharePoint** (search_sharepoint)
"Who is this account?" / metadata lookup → **Snowflake** dimension tables or **Salesforce**

## Business types — STOP and CHECK before querying OOS for a specific account

**Market** = micro-markets, vending → in OOS + Snowflake + LightSpeed + Level
**Delivery** = OCS, pantry, delivery → in Snowflake + LightSpeed ONLY. **NOT in OOS.**

**RULE**: When a user asks about a SPECIFIC account/location AND the question involves OOS data (fill rate, spoilage, OOS, product_activity):
1. Run exactly ONE check: `SELECT DISTINCT "Location" FROM v_daily_oos WHERE "Location" ILIKE '%name%' LIMIT 3`
2. If found → answer the question with OOS data.
3. If NOT found → STOP. Do NOT retry with different spellings. Do NOT run more OOS queries. Instead say: "[Name] doesn't appear in the OOS database — it's likely a Delivery/OCS account. OOS tracking only covers Market locations. Want me to pull their revenue or delivery data from Snowflake instead?"
4. This single-check rule saves time and API calls. Never run more than 1 OOS query to verify a location exists.

## Lookup tools — use dimension tables for metadata

To find a location: `SELECT NAME, LOCATIONTYPE, CHANNEL, REGION FROM DIMLOCATION_V WHERE NAME ILIKE '%keyword%' LIMIT 10`
To find an item: `SELECT NAME, CATEGORY, MANUFACTURER FROM DIMITEM_V WHERE NAME ILIKE '%keyword%' AND DELETED = 'Active' LIMIT 10`
To find a customer: `SELECT NAME, CUSTOMERGROUP FROM DIMCUSTOMER_V WHERE NAME ILIKE '%keyword%' LIMIT 10`
To find an account: `SELECT Name, Type, Industry FROM Account WHERE Name LIKE '%keyword%' LIMIT 10` (Salesforce SOQL)
Multiple matches (e.g. several "House of Representatives") → ask the user which one.

## Item filtering

**OOS views (v_daily_oos, v_daily_oos_details, v_weekly_oos, etc.) are ALREADY pre-filtered.** They exclude Fresh Food, Office items, Condiments, Hot Bev, Seasons, Utensils, Vendor Managed, missing assets, and par=0. Use these views as-is.

**product_activity is RAW — NOT filtered.** When querying it, ALWAYS add:
`WHERE item_category NOT IN ('Fresh Food Breakfast','Fresh Food Entree','Fresh Food Salad','Fresh Food Sandwich','Fresh Food Snack','Condiments','Hot Bev','Seasons','Utensils','Vendor Managed','Equipment Rental','Fee','Office Coffee','Office Tea') AND item NOT LIKE 'HK %' AND item NOT LIKE 'MG %' AND item NOT LIKE 'YS %'`
Only remove these filters if user explicitly asks about fresh food or commissary items.

**Snowflake top/ranking queries** — exclude: `WHERE di.CATEGORY NOT IN ('Equipment Rental','Fee') AND di.NAME NOT LIKE 'HK %' AND di.NAME NOT LIKE 'MG %' AND di.NAME NOT LIKE 'YS %'`

## Hard rules

- LightSpeed has NO price/revenue. Use Snowflake for money questions.
- product_activity has NO date column — it's a rolling 14-day snapshot. Never date-filter it.
- Snowflake date keys are serial integers, NOT dates. Filter with VISITDATETIME/SALEDATETIME timestamps.
- Snowflake fact tables need dimension joins: `JOIN DIMLOCATION_V dl ON f.LOCATIONKEY = dl.LOCATIONKEY` for names.
- OOS view columns are Title Case with spaces — double-quote them: `"Location"`, `"Fill"`, `"OOS"`.
- Row limits: TOP 500 (SQL Server), LIMIT 500 (Snowflake/PostgreSQL), LIMIT 200 (Salesforce).
- Date-filter large tables: oos_details_by_date, dbo.ItemView, Snowflake fact tables.
- On query error, fix and retry silently.
- Snowflake data lags ~1 day (midnight sync). OOS refreshes daily.

## Formulas

Revenue: `SUM(ACTUALSALESEXTENDEDTOTALREVENUE)` | Margin: `SUM(ALLOCATEDSALESEXTENDEDGROSSMARGIN)` | Cost: `SUM(EXTENDEDCOST)`
Fill rate: `"Fill"` from v_daily_oos (0-1, ×100 for %) | OOS count: `"OOS"` from v_daily_oos
Spoilage: `SUM(spoiled_cost)` from product_activity | Shrinkage: `SUM(shrink_cost)` from product_activity
Sell-through: `100.0 * SUM(sold_qty) / NULLIF(SUM(added_qty), 0)` from product_activity
Demand: `"Demand/Day"` from v_daily_oos_details | Days on hand: `"DaysOnHand"` from v_daily_oos_details

## Query patterns

Snowflake revenue by location: `SELECT dl.NAME, ROUND(SUM(f.ACTUALSALESEXTENDEDTOTALREVENUE),2) AS revenue FROM RECOGNIZESALESREVENUEFACT_V f JOIN DIMLOCATION_V dl ON f.LOCATIONKEY=dl.LOCATIONKEY WHERE f.VISITDATETIME>=DATEADD(day,-7,CURRENT_DATE) GROUP BY dl.NAME ORDER BY revenue DESC LIMIT 10`
Snowflake revenue by category: `SELECT di.CATEGORY, ROUND(SUM(f.ACTUALSALESEXTENDEDTOTALREVENUE),2) AS revenue, ROUND(SUM(f.ALLOCATEDSALESEXTENDEDGROSSMARGIN),2) AS margin FROM RECOGNIZESALESREVENUEFACT_V f JOIN DIMITEM_V di ON f.ITEMKEY=di.ITEMKEY WHERE f.VISITDATETIME>=DATE_TRUNC('month',CURRENT_DATE) GROUP BY di.CATEGORY ORDER BY revenue DESC LIMIT 20`
LightSpeed order status: `SELECT statusId, CASE statusId WHEN 1 THEN 'Queried' WHEN 2 THEN 'Queued' WHEN 3 THEN 'Picking' WHEN 4 THEN 'Picked' WHEN 5 THEN 'Printed' WHEN 6 THEN 'Filtered' WHEN 7 THEN 'Staged' END AS status, COUNT(DISTINCT id) AS orders, SUM(quantity) AS total_items FROM dbo.ItemView WHERE orderDate>=CAST(GETDATE() AS DATE) GROUP BY statusId`
OOS fill rates: `SELECT "Location","Route","Fill","OOS" FROM v_daily_oos ORDER BY "Fill" ASC LIMIT 20`
Spoilage: `SELECT item, item_category, location, spoiled_qty, spoiled_cost FROM product_activity WHERE spoiled_qty>0 AND item_category NOT IN ('Fresh Food Breakfast','Fresh Food Entree','Fresh Food Salad','Fresh Food Sandwich','Fresh Food Snack','Condiments','Hot Bev','Seasons','Utensils','Vendor Managed','Equipment Rental','Fee','Office Coffee','Office Tea') AND item NOT LIKE 'HK %' AND item NOT LIKE 'MG %' AND item NOT LIKE 'YS %' ORDER BY spoiled_cost DESC LIMIT 20`
Low stock: `SELECT TOP 20 itemName, itemCode, currentQty, FillTo, ReorderPoint, vendorName FROM dbo.AreaItemParView WHERE itemActive=1 AND currentQty<ReorderPoint AND ReorderPoint>0 ORDER BY (ReorderPoint-currentQty) DESC`
Open tasks: `SELECT Account.Name, Subject, Status, ActivityDate FROM Task WHERE IsClosed=false ORDER BY ActivityDate ASC LIMIT 50`

## Glossary (user term → database)

revenue/sales/money → Snowflake ACTUALSALESEXTENDEDTOTALREVENUE | margin/profit → Snowflake ALLOCATEDSALESEXTENDEDGROSSMARGIN
fill rate → OOS v_daily_oos "Fill" | OOS/out of stock → OOS v_daily_oos "OOS" | spoilage → OOS product_activity spoiled_cost
shrinkage → OOS product_activity shrink_cost | sell-through → OOS product_activity sold/added | demand → OOS v_daily_oos_details "Demand/Day"
inventory/stock → Level AreaItemParView currentQty | par level → Level FillTo, Snowflake PAR, OOS par
orders → LightSpeed dbo.ItemView | picks → LightSpeed dbo.ItemView statusId | POs → Level dbo.PurchaseOrder
accounts → Salesforce Account | cases/installs → Salesforce Case | pipeline → Salesforce Opportunity
location → Snowflake DIMLOCATION_V.NAME | route → Snowflake DIMROUTE_V.NAME | item/product → Snowflake DIMITEM_V.NAME
file/report/document/template/sheet → SharePoint search_sharepoint

## SharePoint files

Three shared document libraries synced locally:
- **Business Intelligence - Documents/** — Reporting (Daily/, Weekly/, Monthly/, Ad Hoc/, Scorecard/), Merchandising/, Pricing/, OCS to Seed/, Processes/, Cases/
- **Customer Operations - Documents/** — Customer-facing docs
- **Standards & Process - Documents/** — SOPs, standards

When returning SharePoint search results, format each file as a clickable markdown download link using the download_url field:
`[filename.xlsx](/api/files/Business%20Intelligence%20-%20Documents/path/to/file.xlsx)` — always use the download_url from the results as-is.
Include the modified date and file size for context.

## Schemas
{schemas}

## Response style

Think out loud while working — 1-2 sentences before each query explaining what you're checking and why. This shows your reasoning.
If a question doesn't fit the account type, explain why instead of running a pointless query.
Lead with the answer. Tables for data (max 8 cols, round to 2 decimals). No filler, no "Great question", no emoji headers.
"""


def _friendly_api_error(e: anthropic.APIError) -> str:
    """Convert raw Anthropic API errors into clean user-facing messages."""
    status = getattr(e, 'status_code', None)

    if status == 400:
        # Bad request — usually a conversation history issue
        return (
            "Something went wrong with our conversation history. "
            "Try asking your question again, or start a new chat if the issue persists."
        )
    if status == 401:
        return "There's a configuration issue on our end. Please notify the admin."
    if status == 429:
        return (
            "I'm getting too many requests right now. "
            "Give me a moment and try again in a few seconds."
        )
    if status == 500 or status == 503:
        return (
            "The AI service is temporarily unavailable. "
            "This usually resolves quickly — try again in a moment."
        )
    if status == 529:
        return (
            "The AI service is currently overloaded. "
            "Please try again in a minute or two."
        )

    # Generic fallback — still clean, no raw error dumps
    return "Something went wrong processing your request. Please try again."


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

    # SharePoint file search — no SQL involved
    if tool_name == "search_sharepoint":
        try:
            results = search_sharepoint_files(
                search_term=tool_input.get("search_term", ""),
                folder=tool_input.get("folder", ""),
                file_type=tool_input.get("file_type", ""),
                modified_after=tool_input.get("modified_after", ""),
                max_results=tool_input.get("max_results", 20),
            )
            return json.dumps(
                {"file_count": len(results), "files": results},
                default=str,
                ensure_ascii=False,
            )
        except Exception as e:
            logger.exception("SharePoint search error")
            return json.dumps({"error": f"SharePoint search error: {str(e)}"})

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
        logger.error("Runtime error in %s: %s", tool_name, e)
        return json.dumps({"error": "Database query failed. The database may be temporarily unavailable."})
    except Exception as e:
        logger.exception("Unexpected error executing tool %s", tool_name)
        return json.dumps({"error": "Could not connect to the database. It may be temporarily unavailable."})


class ChatManager:
    """Manages a chat session with conversation history and Claude API interaction."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history: list[dict] = []
        self.client = anthropic.AsyncAnthropic()  # Uses ANTHROPIC_API_KEY env var
        self.created_at = datetime.now().isoformat()

    def get_history(self) -> list[dict]:
        """Return conversation history for this session."""
        return self.history

    async def send_message(self, user_message: str) -> AsyncGenerator[dict, None]:
        """Send a message and yield streaming event dicts.

        Handles the tool_use loop: when Claude requests a tool, execute it,
        feed the result back, and continue until Claude gives a final text response.

        Yields:
            dict: Event dicts with "type" key:
                - {"type": "chunk", "content": "text"}
                - {"type": "tool_use", "database": "Snowflake", "query": "SELECT ..."}
                - {"type": "status", "content": "Querying Snowflake database..."}
        """
        # Add user message to history and log
        self.history.append({"role": "user", "content": user_message})
        await asyncio.to_thread(log_conversation, self.session_id)
        await asyncio.to_thread(log_message, self.session_id, "user", user_message)

        messages = self._build_messages()
        system_prompt = _build_system_prompt()
        tool_round = 0

        while tool_round < MAX_TOOL_ROUNDS:
            tool_round += 1

            # Collect the full response to detect tool_use blocks
            response_content = []
            text_chunks = []

            try:
                async with self.client.messages.stream(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    system=system_prompt,
                    messages=messages,
                    tools=TOOLS,
                ) as stream:
                    current_text = ""
                    async for event in stream:
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
                                yield {"type": "chunk", "content": chunk}

                    # Get the final message to check for tool use
                    final_message = await stream.get_final_message()
                    response_content = final_message.content

            except anthropic.APIError as e:
                logger.exception("Anthropic API error (status=%s)", getattr(e, 'status_code', '?'))
                error_msg = _friendly_api_error(e)
                yield {"type": "chunk", "content": error_msg}
                self.history.append({"role": "assistant", "content": error_msg})
                return

            # Check if there are any tool_use blocks
            tool_use_blocks = [block for block in response_content if block.type == "tool_use"]

            if not tool_use_blocks:
                # No tool use - conversation turn is complete
                # Save assistant response to history and log
                full_text = "".join(text_chunks)
                if full_text:
                    self.history.append({"role": "assistant", "content": full_text})
                    await asyncio.to_thread(log_message, self.session_id, "assistant", full_text)
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
                    "search_sharepoint": "SharePoint Files",
                }.get(block.name, block.name)

                # Send status event
                status_verb = "Searching" if block.name == "search_sharepoint" else "Querying"
                yield {"type": "status", "content": f"{status_verb} {db_label}..."}

                # Send tool_use metadata so frontend can show query details
                query_text = block.input.get("sql_query") or block.input.get("soql_query") or block.input.get("search_term", "")
                yield {"type": "tool_use", "database": db_label, "query": query_text}

                # Execute the tool in a thread to avoid blocking the event loop
                t0 = time.perf_counter()
                result_str = await asyncio.to_thread(_execute_tool, block.name, block.input)
                duration_ms = int((time.perf_counter() - t0) * 1000)

                # Log the tool call
                try:
                    parsed = json.loads(result_str)
                    rc = parsed.get("row_count") or parsed.get("file_count") or 0
                    err = parsed.get("error")
                except Exception:
                    rc, err = 0, None
                await asyncio.to_thread(
                    log_tool_call, self.session_id, block.name, db_label,
                    query_text, rc, duration_ms, err,
                )

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
        yield {"type": "chunk", "content": "\n\nI've reached the maximum number of database queries for this turn. Please try a more specific question."}
        self.history.append({
            "role": "assistant",
            "content": "I've reached the maximum number of database queries for this turn.",
        })
        self._trim_history()

    def _trim_history(self):
        """Trim history to prevent context window overflow.

        Keeps the last 30 messages while ensuring we never cut in the middle
        of a tool_use/tool_result exchange, which would cause API errors.
        """
        max_messages = 30
        if len(self.history) <= max_messages:
            return

        trimmed = self.history[-max_messages:]

        # The first message must be role=user. If we cut into the middle of
        # an assistant tool_use + user tool_result pair, drop forward until
        # we find a clean user message (plain text, not tool_result).
        while trimmed and (
            trimmed[0]["role"] != "user"
            or (isinstance(trimmed[0]["content"], list)
                and any(b.get("type") == "tool_result" for b in trimmed[0]["content"]))
        ):
            trimmed.pop(0)

        self.history = trimmed

    def _build_messages(self) -> list[dict]:
        """Build the messages list for the Claude API from conversation history."""
        messages = []
        for entry in self.history:
            messages.append({"role": entry["role"], "content": entry["content"]})
        return messages

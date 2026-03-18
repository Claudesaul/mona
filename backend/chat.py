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
    get_lightspeed_connection,
    get_level_connection,
    execute_salesforce_query,
)
from db.schemas import get_schema_description
from tools.definitions import TOOLS

logger = logging.getLogger(__name__)

# Load .env from project root
from pathlib import Path as _Path
load_dotenv(_Path(__file__).resolve().parent.parent / ".env", override=True)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096
MAX_TOOL_ROUNDS = 10  # Prevent infinite tool loops

SYSTEM_PROMPT = f"""You are Mona, a business data assistant for Monumental Markets (vending/micro-market operator, D.C. area).

You answer questions by querying databases. Be direct and concise — no filler, no buzzwords, no long preambles. Answer like a sharp colleague, not a report generator.

## Databases

1. **LightSpeed** (SQL Server) — orders and transactions. Primary view: `dbo.ItemView` (~4.7M rows). Always filter by date.
2. **Level** (SQL Server) — warehouse inventory, par levels, purchase orders. Key view: `dbo.AreaItemParView`.
3. **OOS** (PostgreSQL) — out-of-stock tracking. Main table: `oos_details_by_date` (~12M rows, ALWAYS filter by date). Views: `v_daily_oos` (daily fill %), `v_weekly_oos`, `v_daily_oos_details`. Also `product_activity` — only has ~14 days of data, NO date column to filter on.
4. **Salesforce** (SOQL) — accounts, contacts, tasks, cases, opportunities, leads.

## Schemas
{get_schema_description()}

## Rules

- READ-ONLY. Only SELECT queries.
- SQL Server: use TOP 500. PostgreSQL: use LIMIT 500. Salesforce SOQL: use LIMIT 200.
- ALWAYS date-filter `oos_details_by_date` and `dbo.ItemView`. They are huge.
- `product_activity` has NO date column. It only contains ~14 days of rolling data. Do not try to filter it by date.
- Start with aggregates before drilling down.
- If a query fails, fix it and retry. Don't explain the error at length.

## Response style

- Short and direct. Lead with the answer, not the process.
- Use markdown tables for tabular data. Keep tables clean — no more than 8-10 columns.
- Don't narrate what you're about to do. Just do it.
- Don't use emojis in headers or bullets.
- Skip "Key Takeaways" style sections unless the user asks for analysis.
- When showing the "querying database" status, that's enough context — don't also explain your query strategy in the response text.

Today's date is {datetime.now().strftime('%Y-%m-%d')} ({datetime.now().strftime('%A')}).
"""


def _sanitize_query(sql_query: str) -> str:
    """Validate that a query is read-only and add row limits if missing."""
    query_upper = sql_query.strip().upper()

    # Block write operations
    forbidden = ["INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER ", "TRUNCATE ", "CREATE ", "EXEC ", "EXECUTE "]
    for keyword in forbidden:
        if keyword in query_upper:
            raise ValueError(f"Write operations are not allowed. Blocked keyword: {keyword.strip()}")

    # Ensure it starts with SELECT (or WITH for CTEs)
    if not query_upper.startswith("SELECT") and not query_upper.startswith("WITH"):
        raise ValueError("Only SELECT queries (or WITH/CTE) are allowed.")

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
        try:
            results = execute_salesforce_query(soql_query)
            return json.dumps(
                {"row_count": len(results), "data": results},
                default=str,
                ensure_ascii=False,
            )
        except Exception as e:
            logger.exception("Salesforce query error")
            return json.dumps({"error": f"Salesforce error: {str(e)}"})

    sql_query = tool_input.get("sql_query", "")

    try:
        sql_query = _sanitize_query(sql_query)
    except ValueError as e:
        return json.dumps({"error": str(e)})

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
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        # Serialize results, handling non-JSON-serializable types
        return json.dumps(
            {"row_count": len(results), "data": results},
            default=str,
            ensure_ascii=False,
        )

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

            # Execute each tool and build tool_result messages
            tool_results = []
            for block in tool_use_blocks:
                # Notify user that a query is being executed
                db_label = {
                    "query_lightspeed": "LightSpeed",
                    "query_level": "Level",
                    "query_oos": "OOS (PostgreSQL)",
                    "query_salesforce": "Salesforce",
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

            # Clear text_chunks for the next round
            text_chunks = []

        # If we exhausted tool rounds, add a note
        yield "\n\nI've reached the maximum number of database queries for this turn. Please try a more specific question."
        self.history.append({
            "role": "assistant",
            "content": "I've reached the maximum number of database queries for this turn.",
        })

    def _build_messages(self) -> list[dict]:
        """Build the messages list for the Claude API from conversation history."""
        messages = []
        for entry in self.history:
            messages.append({"role": entry["role"], "content": entry["content"]})
        return messages

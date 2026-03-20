"""Evaluation harness for Mona's text-to-SQL accuracy.

Run: cd backend && venv/Scripts/python.exe eval.py

Tests that Mona routes questions to the correct database and generates
valid SQL patterns. Does NOT execute queries against live databases.
"""

import json
import os
import sys
import re
from datetime import datetime

import anthropic
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from chat import SYSTEM_PROMPT, MODEL, TOOLS

# Test cases: (question, expected_tool, must_contain, must_not_contain)
# must_contain: strings that MUST appear in the generated SQL (case-insensitive)
# must_not_contain: strings that must NOT appear (case-insensitive)
TEST_CASES = [
    # === Snowflake routing ===
    (
        "What was total revenue last week?",
        "query_snowflake",
        ["ACTUALSALESEXTENDEDTOTALREVENUE", "VISITDATETIME"],
        ["VISITDATEKEY >=", "VISITDATEKEY <=", "20260"],  # Must NOT use YYYYMMDD datekeys
    ),
    (
        "Show me revenue by location for March",
        "query_snowflake",
        ["ACTUALSALESEXTENDEDTOTALREVENUE", "DIMLOCATION_V", "VISITDATETIME"],
        [],
    ),
    (
        "What's the gross margin by item category this month?",
        "query_snowflake",
        ["ALLOCATEDSALESEXTENDEDGROSSMARGIN", "DIMITEM_V", "CATEGORY"],
        [],
    ),
    (
        "How much money did we make yesterday?",
        "query_snowflake",
        ["ACTUALSALESEXTENDEDTOTALREVENUE"],
        ["query_lightspeed"],  # Must NOT go to LightSpeed for money questions
    ),
    (
        "Top 10 selling items by revenue",
        "query_snowflake",
        ["DIMITEM_V", "ACTUALSALESEXTENDEDTOTALREVENUE", "LIMIT"],
        [],
    ),

    # === LightSpeed routing ===
    (
        "What's the order status for today?",
        "query_lightspeed",
        ["ItemView", "orderDate", "statusId"],
        ["price", "revenue", "cost"],
    ),
    (
        "How many orders were picked today?",
        "query_lightspeed",
        ["ItemView", "orderDate"],
        [],
    ),

    # === OOS routing ===
    (
        "What locations have the worst fill rate?",
        "query_oos",
        ["v_daily_oos", '"Fill"'],
        [],
    ),
    (
        "Which items are spoiling the most?",
        "query_oos",
        ["product_activity", "spoiled"],
        ["date", "WHERE date", "WHERE \"date\""],  # product_activity has no date column
    ),
    (
        "Show me sell-through percentage by item",
        "query_oos",
        ["product_activity", "sold_qty", "added_qty"],
        ["date"],
    ),
    (
        "What items are out of stock right now?",
        "query_oos",
        [],  # Could use v_daily_oos_details or oos_details_by_date
        [],
    ),
    (
        "Show me the weekly OOS trend",
        "query_oos",
        ["v_weekly_oos"],
        [],
    ),

    # === Level routing ===
    (
        "What's the warehouse inventory for Aquafina?",
        "query_level",
        ["AreaItemParView"],
        [],
    ),
    (
        "Which items are below reorder point?",
        "query_level",
        ["AreaItemParView", "ReorderPoint"],
        [],
    ),

    # === Salesforce routing ===
    (
        "Show me all open tasks",
        "query_salesforce",
        ["Task", "IsClosed"],
        [],
    ),
    (
        "How many customer accounts do we have?",
        "query_salesforce",
        ["Account"],
        [],
    ),

    # === Anti-patterns (things that should NOT happen) ===
    (
        "How much revenue did location ABC make?",
        "query_snowflake",
        ["ACTUALSALESEXTENDEDTOTALREVENUE"],
        [],  # Must NOT go to LightSpeed
    ),
    (
        "What's our shrinkage cost?",
        "query_oos",
        ["product_activity", "shrink"],
        ["date"],  # Must NOT filter product_activity by date
    ),

    # === OOS column quoting ===
    (
        "Show today's fill rates by location",
        "query_oos",
        ['"Fill"', '"Location"'],  # Must double-quote Title Case columns
        [],
    ),

    # === Snowflake date handling ===
    (
        "Revenue for the last 7 days",
        "query_snowflake",
        ["VISITDATETIME"],
        ["VISITDATEKEY >="],  # Must NOT use datekey for filtering
    ),
]


def run_eval():
    """Run evaluation and print results."""
    client = anthropic.Anthropic()

    passed = 0
    failed = 0
    errors = []

    print(f"Running {len(TEST_CASES)} evaluation tests...\n")
    print(f"Model: {MODEL}")
    print(f"System prompt length: {len(SYSTEM_PROMPT)} chars\n")
    print("-" * 80)

    for i, (question, expected_tool, must_contain, must_not_contain) in enumerate(TEST_CASES, 1):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": question}],
                tools=TOOLS,
            )

            # Find tool_use block
            tool_use = None
            for block in response.content:
                if block.type == "tool_use":
                    tool_use = block
                    break

            if tool_use is None:
                errors.append((i, question, "No tool_use block generated"))
                failed += 1
                print(f"  FAIL #{i}: {question}")
                print(f"    Error: No tool_use block — model responded with text only")
                continue

            actual_tool = tool_use.name
            sql = tool_use.input.get("sql_query", tool_use.input.get("soql_query", ""))
            sql_upper = sql.upper()

            # Check tool routing
            issues = []
            if actual_tool != expected_tool:
                issues.append(f"Wrong tool: expected {expected_tool}, got {actual_tool}")

            # Check must_contain
            for pattern in must_contain:
                if pattern.upper() not in sql_upper and pattern not in sql:
                    issues.append(f"Missing: '{pattern}'")

            # Check must_not_contain
            for pattern in must_not_contain:
                if pattern.upper() in sql_upper or pattern in sql:
                    issues.append(f"Unexpected: '{pattern}'")

            if issues:
                failed += 1
                print(f"  FAIL #{i}: {question}")
                for issue in issues:
                    print(f"    - {issue}")
                print(f"    Tool: {actual_tool}")
                print(f"    SQL: {sql[:200]}")
                errors.append((i, question, issues))
            else:
                passed += 1
                print(f"  PASS #{i}: {question}")
                print(f"    Tool: {actual_tool}")

        except Exception as e:
            failed += 1
            errors.append((i, question, str(e)))
            print(f"  ERROR #{i}: {question}")
            print(f"    {str(e)[:200]}")

    print("\n" + "=" * 80)
    print(f"\nResults: {passed}/{passed + failed} passed ({100 * passed / (passed + failed):.0f}%)")

    if errors:
        print(f"\nFailed tests:")
        for num, q, issue in errors:
            print(f"  #{num}: {q}")
            if isinstance(issue, list):
                for i in issue:
                    print(f"    - {i}")
            else:
                print(f"    - {issue}")

    return passed, failed


if __name__ == "__main__":
    passed, failed = run_eval()
    sys.exit(0 if failed == 0 else 1)

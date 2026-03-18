"""Database schema descriptions for Claude system prompt.

Compact format to minimize token usage while giving the AI enough
context to write correct queries across 5 databases.
"""

SCHEMAS = {
    "snowflake": {
        "name": "Snowflake (SEED Data Warehouse)",
        "type": "Snowflake SQL",
        "description": "PRIMARY source for revenue, sales, fulfillment, and operational analytics. All fact tables join to dimension tables via KEY columns. Date keys are integers in YYYYMMDD format.",
        "tables": {
            "RECOGNIZESALESREVENUEFACT_V": {
                "description": "Revenue and sales per visit/delivery. THE table for financial questions.",
                "columns": "LOCATIONKEY (INT FK), ITEMKEY (INT FK), ROUTEKEY (INT FK), VISITDATEKEY (INT, YYYYMMDD), VISITDATETIME (TIMESTAMP), SALETYPE (TEXT), QUANTITYSOLD (NUM), ACTUALSALESBASEPRICE (NUM), ACTUALSALESEXTENDEDPRICE (NUM), ACTUALSALESEXTENDEDTOTALREVENUE (NUM — use this for revenue), ALLOCATEDSALESEXTENDEDTOTALREVENUE (NUM), EXTENDEDCOST (NUM), ALLOCATEDSALESEXTENDEDGROSSMARGIN (NUM — gross margin), NUMBERSPOILED (NUM), EXTENDEDSPOILEDVALUE (NUM), DELIVEREDQUANTITY (NUM), EXTENDEDCOMMISSIONVALUE (NUM)",
                "joins": ["DIMLOCATION_V ON LOCATIONKEY", "DIMITEM_V ON ITEMKEY", "DIMROUTE_V ON ROUTEKEY"],
                "notes": ["Always filter by VISITDATEKEY (YYYYMMDD integer) or VISITDATETIME.", "Revenue = ACTUALSALESEXTENDEDTOTALREVENUE."],
            },
            "MICROMARKETSALESFACT_V": {
                "description": "Individual micro market sale transactions (20M+ rows).",
                "columns": "LOCATIONKEY (INT FK), ITEMKEY (INT FK), SALEDATEKEY (INT, YYYYMMDD), SALEDATETIME (TIMESTAMP), QUANTITY (NUM), EXTENDEDPRICE (NUM), EXTENDEDTOTALPRICE (NUM), PRODUCTCOST (NUM), DEPLETION (NUM), WASOUTOFSTOCK (TEXT), WASDEPLETED (TEXT), CURRENTINVENTORY (NUM)",
                "joins": ["DIMLOCATION_V ON LOCATIONKEY", "DIMITEM_V ON ITEMKEY"],
                "notes": ["Always filter by SALEDATEKEY or SALEDATETIME."],
            },
            "ORDERTOFULFILLMENTVENDINGMARKETFACT_V": {
                "description": "Order-to-fulfillment tracking (31M+ rows). Orders, picks, deliveries, spoils.",
                "columns": "LOCATIONKEY (INT FK), ITEMKEY (INT FK), TARGETDELIVERYDATEKEY (INT, YYYYMMDD), DELIVERYDATEKEY (INT), ORDERQUANTITY (NUM), PICKQUANTITY (NUM), DELIVEREDQUANTITY (NUM), SPOILQUANTITY (NUM), REMOVEQUANTITY (NUM), DEPLETIONQUANTITY (NUM), COILOOS (NUM), PAR (NUM), CAPACITY (NUM), ITEMCOST (NUM), DELIVERYDRIVERNAME (TEXT)",
                "joins": ["DIMLOCATION_V ON LOCATIONKEY", "DIMITEM_V ON ITEMKEY"],
                "notes": ["Always filter by TARGETDELIVERYDATEKEY or DELIVERYDATEKEY."],
            },
            "SALESBYCOILFACT_V": {
                "description": "Sales metrics by coil position (47M+ rows). Daily sales averages and inventory.",
                "columns": "LOCATIONKEY (INT FK), ITEMKEY (INT FK), EXTRACTDATEKEY (INT, YYYYMMDD), PAR (NUM), ACTUALSALESTODAYVALUE (NUM), AVERAGEDAILYSALESVALUE (NUM), ACTUALVENDPRICEVALUE (NUM — vend price), INVENTORY (NUM)",
                "joins": ["DIMLOCATION_V ON LOCATIONKEY", "DIMITEM_V ON ITEMKEY"],
                "notes": ["Always filter by EXTRACTDATEKEY."],
            },
            "DIMITEM_V": {
                "description": "Item/product dimension (6.4K items).",
                "columns": "ITEMKEY (INT PK), NAME (TEXT), CODE (TEXT), CATEGORY (TEXT), MANUFACTURER (TEXT), UNITCOST (NUM), SIZE (TEXT), SHELFLIFE (NUM)",
            },
            "DIMLOCATION_V": {
                "description": "Location/site dimension (1.7K locations).",
                "columns": "LOCATIONKEY (INT PK), NAME (TEXT), CODE (TEXT), CITY (TEXT), STATE (TEXT), REGION (TEXT), CHANNEL (TEXT), LOCATIONTYPE (TEXT), COMMISSIONPLANNAME (TEXT), PRICINGPLANNAME (TEXT)",
            },
            "DIMROUTE_V": {
                "description": "Delivery route dimension (65 routes).",
                "columns": "ROUTEKEY (INT PK), NAME (TEXT), CODE (TEXT), DRIVERNAME (TEXT)",
            },
            "WAREHOUSEINVENTORYFACT_V": {
                "description": "Warehouse inventory snapshots (8M+ rows).",
                "columns": "ITEMKEY (INT FK), EXTRACTDATEKEY (INT), QUANTITYONHAND (NUM), QUANTITYCOMMITTED (NUM)",
            },
        },
    },
    "lightspeed": {
        "name": "LightSpeed (SQL Server)",
        "type": "T-SQL",
        "description": "Order and pick status tracking. WARNING: Has NO price/cost/revenue columns. Do NOT use for financial questions — use Snowflake instead.",
        "tables": {
            "dbo.ItemView": {
                "description": "Order line items (~4.7M rows). Shows what was ordered, picked, and delivered. No financial data.",
                "columns": "id (INT), locID (INT), locDescription (TEXT — location name), machineBarcode (TEXT), orderDate (DATE), product (TEXT — item name), productID (INT), quantity (INT — ordered qty), updatedQuantity (INT), cQty (INT — current qty), sQty (INT — sold qty), par (INT), capacity (INT), coil (TEXT), statusId (INT — order status), rteID (INT), rteDescription (TEXT — route name), PickDate (DATE), completedTime (DATETIME), providerName (TEXT), categoryID (INT), cusDescription (TEXT — customer name)",
                "notes": [
                    "WARNING: No price, cost, or revenue columns. Cannot answer 'how much money' questions.",
                    "Use for: order status, what was ordered/picked, fulfillment tracking.",
                    "Always filter by orderDate — table is huge.",
                ],
            },
        },
    },
    "level": {
        "name": "Level (SQL Server)",
        "type": "T-SQL",
        "description": "Warehouse inventory, par levels, and purchase orders.",
        "tables": {
            "dbo.AreaItemParView": {
                "description": "Current inventory and par levels by warehouse area (~5K rows).",
                "columns": "itemID (INT), itemName (TEXT), itemCode (TEXT), itemActive (BIT), FillTo (INT — par level), ReorderPoint (INT), SafetyStock (INT), currentQty (INT — on hand), AreaID (INT), areaName (TEXT — warehouse area), vendorName (TEXT)",
            },
            "dbo.PurchaseOrder": {
                "description": "Purchase orders (~27K rows).",
                "columns": "ID (INT), vendorID (INT), voided (BIT), received (BIT), expectedReceiptDate (DATE)",
            },
            "dbo.Item": {
                "description": "Product master (~7.4K items).",
                "columns": "ID (INT), Name (TEXT), Code (TEXT), active (BIT), cost (MONEY)",
            },
        },
    },
    "oos": {
        "name": "OOS (PostgreSQL)",
        "type": "PostgreSQL",
        "description": "Out-of-stock tracking, fill rates, and product activity.",
        "tables": {
            "oos_details_by_date": {
                "description": "Coil-level stock readings (~12M rows). One row per coil per date.",
                "columns": "location (TEXT), route (TEXT), asset_id (TEXT), asset_type (TEXT), coil (NUM), item_category (TEXT), item_code (TEXT), item (TEXT), price (NUM — retail price), par (NUM), current_level (NUM — 0 means OOS), date (TIMESTAMP)",
                "notes": ["ALWAYS filter by date. current_level = 0 means out of stock."],
            },
            "product_activity": {
                "description": "Rolling ~14-day product movement snapshot. Spoilage, shrinkage, sales velocity.",
                "columns": "location (TEXT), item (TEXT), item_code (TEXT), item_category (TEXT), added_qty (INT), sold_qty (INT), shrink_qty (INT), shrink_cost (NUM), spoiled_qty (INT), spoiled_cost (NUM), removed_qty (INT), market_price (NUM), commission_price (NUM), market_pricing_type (TEXT)",
                "notes": [
                    "NO date column. Do NOT filter by date. Entire table = last ~14 days.",
                    "Sell-through % = 100.0 * sold_qty / NULLIF(added_qty, 0)",
                    "Use for: spoilage rankings, shrinkage analysis, slow/fast movers.",
                ],
            },
            "v_daily_oos": {
                "description": "Daily OOS summary by location.",
                "columns": "location (TEXT), route (TEXT), date (DATE), total_coils (INT), oos_coils (INT), oos_percentage (NUM)",
            },
            "v_weekly_oos": {
                "description": "Weekly OOS summary by location.",
                "columns": "location (TEXT), route (TEXT), week_start (DATE), avg_oos_percentage (NUM)",
            },
            "v_daily_oos_details": {
                "description": "Coil-level OOS details (items that are out of stock).",
                "columns": "location (TEXT), route (TEXT), asset_id (TEXT), coil (TEXT), item (TEXT), par (INT), date (DATE)",
            },
        },
    },
    "salesforce": {
        "name": "Salesforce",
        "type": "SOQL",
        "description": "CRM — accounts, contacts, tasks, cases, opportunities.",
        "tables": {
            "Account": {
                "description": "Customer accounts (~2K).",
                "columns": "Id, Name, Type, BillingCity, BillingState, Industry, OwnerId, CreatedDate",
            },
            "Contact": {
                "description": "People at accounts (~5K).",
                "columns": "Id, Name, Email, Phone, Title, AccountId (FK → Account)",
            },
            "Task": {
                "description": "Tasks/activities (~12K).",
                "columns": "Id, Subject, Status, Priority, ActivityDate, Description, AccountId, OwnerId, IsClosed",
            },
            "Case": {
                "description": "Support cases (~44K).",
                "columns": "Id, Subject, Status, Priority, AccountId, ContactId, CreatedDate, ClosedDate",
            },
            "Opportunity": {
                "description": "Sales opportunities (~4K).",
                "columns": "Id, Name, StageName, Amount, CloseDate, AccountId, OwnerId",
            },
        },
    },
}


def get_schema_description() -> str:
    """Generate compact schema description for the system prompt."""
    lines = []

    for db_info in SCHEMAS.values():
        lines.append(f"\n### {db_info['name']} ({db_info['type']})")
        lines.append(db_info["description"])

        for table_name, t in db_info["tables"].items():
            lines.append(f"\n**{table_name}**: {t['description']}")
            lines.append(f"  Columns: {t['columns']}")

            if "joins" in t:
                lines.append(f"  Joins: {', '.join(t['joins'])}")

            if "notes" in t:
                for note in t["notes"]:
                    lines.append(f"  * {note}")

    return "\n".join(lines)

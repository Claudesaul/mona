"""Database schema descriptions for Claude system prompt.

Compact format to minimize token usage while giving the AI enough
context to write correct queries across 5 databases.
"""

SCHEMAS = {
    "snowflake": {
        "name": "Snowflake (SEED Data Warehouse)",
        "type": "Snowflake SQL",
        "description": (
            "PRIMARY source for revenue, sales, fulfillment, and operational analytics. "
            "All fact tables join to dimension tables via KEY columns. "
            "Date keys are SERIAL INTEGERS (days since 1899-12-31), NOT YYYYMMDD. "
            "Use TIMESTAMP columns (VISITDATETIME, SALEDATETIME) for date filtering instead. "
            "Data range: Jan 2024 – present."
        ),
        "tables": {
            "RECOGNIZESALESREVENUEFACT_V": {
                "description": "Revenue and sales per visit/delivery (29.6M rows). THE table for financial questions.",
                "columns": (
                    "LOCATIONKEY (INT FK), ITEMKEY (INT FK), ROUTEKEY (INT FK), CUSTOMERKEY (INT FK), "
                    "MACHINEKEY (INT FK), VISITDATEKEY (INT, serial date — do NOT use for filtering), "
                    "VISITDATETIME (TIMESTAMP — use this for date filtering), "
                    "SALETYPE (TEXT: 'Day' or 'Visit'), QUANTITYSOLD (NUM), "
                    "ACTUALSALESBASEPRICE (NUM — unit price), ACTUALSALESEXTENDEDPRICE (NUM), "
                    "ACTUALSALESEXTENDEDTOTALREVENUE (NUM — use for revenue), "
                    "ALLOCATEDSALESEXTENDEDTOTALREVENUE (NUM), "
                    "EXTENDEDCOST (NUM), ALLOCATEDSALESEXTENDEDGROSSMARGIN (NUM — gross margin), "
                    "EXTENDEDTAX (NUM), EXTENDEDDISCOUNT (NUM), EXTENDEDSURCHARGE (NUM), "
                    "NUMBERSPOILED (NUM), EXTENDEDSPOILEDVALUE (NUM), "
                    "EXTENDEDCOMMISSIONVALUE (NUM), DELIVEREDQUANTITY (NUM), "
                    "SERVICEBYUSERNAME (TEXT — driver name)"
                ),
                "joins": ["DIMLOCATION_V ON LOCATIONKEY", "DIMITEM_V ON ITEMKEY", "DIMROUTE_V ON ROUTEKEY"],
                "notes": [
                    "Filter by VISITDATETIME (timestamp), NOT VISITDATEKEY.",
                    "Revenue = SUM(ACTUALSALESEXTENDEDTOTALREVENUE).",
                    "Gross margin = SUM(ALLOCATEDSALESEXTENDEDGROSSMARGIN).",
                ],
            },
            "MICROMARKETSALESFACT_V": {
                "description": "Individual micro market sale transactions (20.3M rows).",
                "columns": (
                    "LOCATIONKEY (INT FK), ITEMKEY (INT FK), MICROMARKETKEY (INT FK), "
                    "SALEDATEKEY (INT, serial date — do NOT use for filtering), "
                    "SALEDATETIME (TIMESTAMP — use this for date filtering), "
                    "QUANTITY (NUM), EXTENDEDPRICE (NUM), EXTENDEDTOTALPRICE (NUM), "
                    "PRODUCTCOST (NUM), CAPACITY (NUM), PAR (NUM), "
                    "DEPLETION (NUM), CURRENTINVENTORY (NUM), "
                    "WASOUTOFSTOCK (TEXT), WASDEPLETED (TEXT)"
                ),
                "joins": ["DIMLOCATION_V ON LOCATIONKEY", "DIMITEM_V ON ITEMKEY"],
                "notes": ["Filter by SALEDATETIME, NOT SALEDATEKEY."],
            },
            "ORDERTOFULFILLMENTVENDINGMARKETFACT_V": {
                "description": "Order-to-fulfillment tracking (31.8M rows). Orders, picks, deliveries, spoils.",
                "columns": (
                    "LOCATIONKEY (INT FK), ITEMKEY (INT FK), MACHINEKEY (INT FK), "
                    "TARGETDELIVERYDATEKEY (INT, serial date), PICKDATEKEY (INT), DELIVERYDATEKEY (INT), "
                    "ORDERQUANTITY (NUM), PICKQUANTITY (NUM), DELIVEREDQUANTITY (NUM), "
                    "SPOILQUANTITY (NUM), REMOVEQUANTITY (NUM), "
                    "DEPLETIONQUANTITY (NUM), COILOOS (NUM), PAR (NUM), CAPACITY (NUM), "
                    "ITEMCOST (NUM), DELIVERYDRIVERNAME (TEXT), "
                    "REASONFORSCHEDULE (TEXT), HASPOGCHANGE (TEXT)"
                ),
                "joins": ["DIMLOCATION_V ON LOCATIONKEY", "DIMITEM_V ON ITEMKEY"],
                "notes": [
                    "No TIMESTAMP column — must convert datekeys: DATEADD(day, DELIVERYDATEKEY, '1899-12-31').",
                    "Or filter with: DELIVERYDATEKEY = DATEDIFF(day, '1899-12-31', '2026-03-20').",
                ],
            },
            "SALESBYCOILFACT_V": {
                "description": "Sales metrics by coil position (47.9M rows). Daily sales averages and inventory.",
                "columns": (
                    "LOCATIONKEY (INT FK), ITEMKEY (INT FK), MACHINEKEY (INT FK), "
                    "EXTRACTDATEKEY (INT, serial date), PAR (NUM), "
                    "ACTUALSALESTODAYVALUE (NUM), AVERAGEDAILYSALESVALUE (NUM), "
                    "ACTUALVENDPRICEVALUE (NUM — vend price), INVENTORY (NUM), "
                    "AVERAGESUNDAYSALESVALUE (NUM), AVERAGEMONDAYSALESVALUE (NUM), "
                    "AVERAGETUESDAYSALESVALUE (NUM), AVERAGEWEDNESDAYSALESVALUE (NUM), "
                    "AVERAGETHURSDAYSALESVALUE (NUM), AVERAGEFRIDAYSALESVALUE (NUM), "
                    "AVERAGESATURDAYSALESVALUE (NUM)"
                ),
                "joins": ["DIMLOCATION_V ON LOCATIONKEY", "DIMITEM_V ON ITEMKEY"],
                "notes": ["No TIMESTAMP — use DATEADD(day, EXTRACTDATEKEY, '1899-12-31') for date conversion."],
            },
            "DIMITEM_V": {
                "description": "Item/product dimension (6.4K items).",
                "columns": (
                    "ITEMKEY (INT PK), ITEMID (INT), CODE (TEXT), NAME (TEXT), CATEGORY (TEXT), "
                    "MANUFACTURER (TEXT), COMMISSIONCATEGORY (TEXT), UNITCOST (NUM), "
                    "SIZE (TEXT), COUNT (NUM), SHELFLIFE (NUM), "
                    "CURRENTROWINDICATOR (TEXT — 'Current' for active), DELETED (TEXT — 'Active' or 'Deleted')"
                ),
            },
            "DIMLOCATION_V": {
                "description": "Location/site dimension (1.7K locations).",
                "columns": (
                    "LOCATIONKEY (INT PK), LOCATIONID (INT), CUSTOMERKEY (INT FK), "
                    "NAME (TEXT), CODE (TEXT), ADDRESS1 (TEXT), CITY (TEXT), STATE (TEXT), ZIP (TEXT), "
                    "REGION (TEXT), CHANNEL (TEXT), LOCATIONTYPE (TEXT), "
                    "COMMISSIONPLANNAME (TEXT), PRICINGPLANNAME (TEXT), "
                    "MANAGEMENTACCOUNTNAME (TEXT), MANAGEMENTCOMPANYNAME (TEXT), "
                    "PRIMARYCONSUMERTYPE (TEXT), "
                    "GEOCODELATITUDE (FLOAT), GEOCODELONGITUDE (FLOAT), "
                    "CURRENTROWINDICATOR (TEXT), DELETED (TEXT)"
                ),
            },
            "DIMROUTE_V": {
                "description": "Delivery route dimension (65 routes).",
                "columns": "ROUTEKEY (INT PK), ROUTEID (INT), NAME (TEXT), CODE (TEXT), DRIVERNAME (TEXT), DELETED (TEXT)",
            },
            "DIMCUSTOMER_V": {
                "description": "Customer/account dimension (551 customers).",
                "columns": (
                    "CUSTOMERKEY (INT PK), CUSTOMERID (INT), NAME (TEXT), "
                    "CITY (TEXT), STATE (TEXT), ZIP (TEXT), "
                    "CUSTOMERGROUP (TEXT), ACCOUNTMANAGERUSERNAME (TEXT), "
                    "SALESPERSONUSERNAME (TEXT), MANAGEMENTCOMPANYNAME (TEXT)"
                ),
            },
            "WAREHOUSEINVENTORYFACT_V": {
                "description": "Warehouse inventory snapshots (8.3M rows).",
                "columns": (
                    "WAREHOUSEKEY (INT FK), ITEMKEY (INT FK), "
                    "INVENTORYDATEKEY (INT, serial date), INVENTORYTIME (TIMESTAMP), "
                    "CURRENTPERPETUALINVENTORYEACHES (NUM — qty on hand), "
                    "CURRENTPERPETUALINVENTORYVALUE (NUM — $ value), "
                    "PARLEVELPACKVALUE (NUM), PARLEVELEACHES (NUM)"
                ),
                "joins": ["DIMITEM_V ON ITEMKEY", "DIMWAREHOUSE_V ON WAREHOUSEKEY"],
            },
        },
    },
    "lightspeed": {
        "name": "LightSpeed (SQL Server)",
        "type": "T-SQL",
        "description": (
            "Order and pick status tracking. WARNING: Has NO price/cost/revenue columns. "
            "Do NOT use for financial questions — use Snowflake instead. "
            "Data range: Dec 2025 – present (~3 months rolling)."
        ),
        "tables": {
            "dbo.ItemView": {
                "description": "Order line items (4.8M rows). Shows what was ordered, picked, and delivered. No financial data.",
                "columns": (
                    "id (INT — order ID), locID (TEXT), locDescription (TEXT — location name), "
                    "cusDescription (TEXT — customer name), rteID (TEXT), rteDescription (TEXT — route name), "
                    "machineBarcode (TEXT), machineCategory (TEXT — e.g. 'Seed: Combo Cooler'), "
                    "orderDate (DATETIME), PickDate (DATETIME), completedTime (DATETIME), "
                    "product (TEXT — item name), productID (TEXT), categoryID (TEXT — category name), "
                    "quantity (INT — ordered qty), updatedQuantity (INT — picked qty), "
                    "cQty (INT — case qty), sQty (INT — shipped qty), "
                    "par (INT), capacity (INT), coil (TEXT — 'deliveryEach' or 'deliveryCase'), "
                    "statusId (INT — 1=Queried 2=Queued 3=Picking 4=Picked 5=Printed 6=Filtered 7=Staged), "
                    "providerName (TEXT), empID (INT), SecondsToPick (INT), "
                    "branchId (INT), sentToLevel (INT)"
                ),
                "notes": [
                    "WARNING: No price, cost, or revenue columns. Cannot answer 'how much money' questions.",
                    "Always filter by orderDate — table is huge.",
                    "statusId values: 1=Queried, 2=Queued, 3=Picking, 4=Picked, 5=Printed, 6=Filtered, 7=Staged.",
                ],
            },
            "dbo.OrderTotals": {
                "description": "Aggregated order-level summary. Good for order efficiency analysis.",
                "columns": (
                    "orderedQuantity (INT), pickedQuantity (INT), nolightQuantity (INT), "
                    "elapsedTotalSeconds (INT), elapsedTimeString (TEXT)"
                ),
            },
            "dbo.RouteTotals": {
                "description": "Route-level aggregates for performance analysis.",
                "columns": (
                    "totalPicked (INT), noLightQuantity (INT), orders (INT), "
                    "SnackTotes (INT), XBINTotes (INT), totalSeconds (INT), "
                    "startTime (DATETIME), endTime (DATETIME)"
                ),
            },
        },
    },
    "level": {
        "name": "Level (SQL Server)",
        "type": "T-SQL",
        "description": "Warehouse inventory, par levels, purchase orders, receiving, and vendor management.",
        "tables": {
            "dbo.AreaItemParView": {
                "description": "Current inventory and par levels by warehouse area (4.9K rows).",
                "columns": (
                    "itemID (INT), itemName (NVARCHAR — product name), itemCode (NVARCHAR), "
                    "itemActive (BIT), FillTo (INT — par level), ReorderPoint (INT), "
                    "SafetyStock (INT), currentQty (INT — on hand), "
                    "AreaID (INT), areaName (NVARCHAR — warehouse area), "
                    "vendorName (NVARCHAR — comma-separated vendor list), "
                    "DaysToFillTo (INT), lastUpdate (DATETIME)"
                ),
            },
            "dbo.QohByArea": {
                "description": "Quantity on hand by storage area with fill-to levels (1.6K rows).",
                "columns": (
                    "areaID (INT), StorageArea (NVARCHAR), itemID (INT), ItemName (NVARCHAR), "
                    "QOH (INT — quantity on hand), Category (NVARCHAR), ItemCode (NVARCHAR), FillTo (INT)"
                ),
            },
            "dbo.PurchaseOrder": {
                "description": "Purchase orders (26.7K rows). Date range: 2016 – present.",
                "columns": (
                    "ID (INT), vendorID (INT FK), voided (BIT), received (BIT), "
                    "orderDate (DATETIME), expectedReceiptDate (DATETIME), "
                    "branchId (INT), Comments (VARCHAR), Submitted (BIT)"
                ),
            },
            "dbo.Item": {
                "description": "Product master (7.4K items).",
                "columns": (
                    "ID (INT), Name (NVARCHAR), Code (NVARCHAR), active (BIT), "
                    "cost (MONEY), itemCategoryID (INT FK), "
                    "shelfLifeDays (INT), minimumRemainingShelfLifeDays (INT)"
                ),
            },
            "dbo.Vendor": {
                "description": "Vendor master (178 vendors).",
                "columns": "id (INT), Name (NVARCHAR), Code (NVARCHAR), active (BIT)",
            },
            "dbo.ReceiptView": {
                "description": "Receiving history with costs (273K rows). Shows what was received from vendors.",
                "columns": (
                    "receiptID (INT), vendorID (INT), vendor (NVARCHAR — vendor name), "
                    "transactionDate (DATETIME), receiptDate (DATETIME), "
                    "quantity (INT — cases), extendedQuantity (INT — eaches), "
                    "product (NVARCHAR — item name), itemID (INT), "
                    "cost (MONEY — case cost), sizeCost (MONEY — unit cost), "
                    "storageArea (NVARCHAR), validated (BIT), voided (BIT)"
                ),
            },
            "dbo.PoiView": {
                "description": "PO line items with pricing and velocity (557K rows).",
                "columns": (
                    "id (INT), purchaseOrderID (INT FK), itemName (NVARCHAR), itemCode (NVARCHAR), "
                    "quantity (INT), expectedCost (MONEY), "
                    "ItemSizeVendorBranchPrice (MONEY), branchExtendedPrice (MONEY), "
                    "extendedQuantity (INT), itemQoh (INT — current qty), "
                    "itemFillTo (INT — par), AvgVelocityItmBranch30Day (FLOAT), "
                    "CurrentDaysSupply (FLOAT), DaysOnOrder (FLOAT), "
                    "SizeDescription (NVARCHAR — e.g. 'Case', 'Pallet'), sizeUnits (INT)"
                ),
            },
            "dbo.ItemCategory": {
                "description": "Product categories (115 categories).",
                "columns": "id (INT), Name (NVARCHAR), active (BIT)",
            },
        },
    },
    "oos": {
        "name": "OOS (PostgreSQL)",
        "type": "PostgreSQL",
        "description": (
            "Out-of-stock tracking, fill rates, and product activity. "
            "Data range: Nov 2025 – present (~4 months). "
            "Note: column names in views use Title Case with spaces (e.g. \"Sold Qty\")."
        ),
        "tables": {
            "oos_details_by_date": {
                "description": "Coil-level stock readings (12.5M rows). One row per coil per date.",
                "columns": (
                    "id (INT), location (TEXT), route (TEXT), asset_id (TEXT), asset_type (TEXT), "
                    "coil (NUM), shelf (NUM), position (NUM), "
                    "item_category (TEXT), item_code (TEXT), item (TEXT), "
                    "price (NUM — retail price), par (NUM), "
                    "current_level (NUM — 0 means OOS), date (TIMESTAMP)"
                ),
                "notes": ["ALWAYS filter by date. current_level = 0 means out of stock."],
            },
            "product_activity": {
                "description": "Rolling ~14-day product movement snapshot (152K rows). Spoilage, shrinkage, sales velocity.",
                "columns": (
                    "id (INT), location (TEXT), item (TEXT), item_code (TEXT), item_category (TEXT), "
                    "added_qty (INT), sold_qty (INT), shrink_qty (INT), shrink_cost (NUM), "
                    "spoiled_qty (INT), spoiled_cost (NUM), removed_qty (INT), "
                    "market_pricing_type (TEXT — 'Standard'/'Commission'/'Custom'), "
                    "market_price (NUM), commission_price (NUM)"
                ),
                "notes": [
                    "NO date column. Do NOT filter by date. Entire table = last ~14 days.",
                    "Sell-through % = 100.0 * sold_qty / NULLIF(added_qty, 0)",
                    "Use for: spoilage rankings, shrinkage analysis, slow/fast movers.",
                ],
            },
            "v_daily_oos": {
                "description": "Today's OOS summary by location (523 rows).",
                "columns": '"Location" (TEXT), "Route" (TEXT), "Fill" (NUM — fill rate 0-1), "OOS" (BIGINT — count of OOS coils), "Note" (TEXT)',
                "notes": ["Column names are Title Case. Use double quotes: SELECT \"Location\", \"Fill\" FROM v_daily_oos"],
            },
            "v_weekly_oos": {
                "description": "Weekly OOS count by location (3K rows).",
                "columns": '"Location" (TEXT), "Week" (TEXT — e.g. \'08-Mar\'), "OOS" (BIGINT)',
                "notes": ["Week is a text label like '08-Mar', not a date."],
            },
            "v_daily_oos_details": {
                "description": "Today's OOS coil details with demand metrics (1K rows).",
                "columns": (
                    '"Location" (TEXT), "Asset ID" (TEXT), "Coil" (NUM), '
                    '"Item Code" (TEXT), "Item" (TEXT), "Par" (NUM), '
                    '"Sold Qty" (INT), "Spoiled Qty" (INT), "Shrink Qty" (INT), '
                    '"Demand/Day" (NUM), "DaysOnHand" (NUM)'
                ),
                "notes": ["Column names have spaces — must use double quotes."],
            },
            "v_future_daily_oos": {
                "description": "Predicted shorts by location (485 rows).",
                "columns": '"LOC" (TEXT), "shorts" (BIGINT)',
            },
            "v_this_week_oos_details": {
                "description": "Current week's OOS details (5.9K rows).",
                "columns": '"Location" (TEXT), "Asset ID" (TEXT), "Coil" (NUM), "Item Code" (TEXT), "Item" (TEXT), "Item Category" (TEXT), "Par" (NUM), "Curr_Lvl" (NUM), "Date" (DATE)',
            },
            "v_last_week_oos_details": {
                "description": "Last week's OOS details (6.2K rows).",
                "columns": '"Location" (TEXT), "Asset ID" (TEXT), "Route" (TEXT), "Coil" (NUM), "Item Code" (TEXT), "Item" (TEXT), "Item Category" (TEXT), "Par" (NUM), "Curr_Lvl" (NUM), "Date" (DATE)',
            },
            "v_weekly_oos_pivot": {
                "description": "Weekly OOS pivot table by location (526 rows). Columns are dynamic week labels.",
                "columns": '"Location" (TEXT), then 6 week columns (e.g. "08-Mar"), "Total" (NUM)',
            },
        },
    },
    "salesforce": {
        "name": "Salesforce",
        "type": "SOQL",
        "description": "CRM — accounts, contacts, tasks, cases, opportunities.",
        "tables": {
            "Account": {
                "description": "Customer accounts (2,092 — 1,060 customers, 981 prospects).",
                "columns": (
                    "Id, Name, Type (picklist: Customer/Prospect/Partner/Other), "
                    "BillingCity, BillingState, Industry, Phone, Website, "
                    "OwnerId, CreatedDate, ParentId"
                ),
            },
            "Contact": {
                "description": "People at accounts (5.4K).",
                "columns": "Id, FirstName, LastName, Name, Email, Phone, MobilePhone, Title, Department, AccountId (FK → Account)",
            },
            "Task": {
                "description": "Tasks/activities (12.4K). Status: Open/Completed/In Progress/On Hold.",
                "columns": "Id, Subject, Status, Priority, ActivityDate, Description, AccountId, OwnerId, IsClosed",
            },
            "Case": {
                "description": "Cases (44K). Mostly equipment installs/removals, not support tickets. Status: Closed/Removed/Installed/New/etc.",
                "columns": (
                    "Id, CaseNumber, Subject, Status, Priority, Type, Reason, Origin, "
                    "AccountId, ContactId, OwnerId, CreatedDate, ClosedDate, IsClosed"
                ),
            },
            "Opportunity": {
                "description": "Sales opportunities (4K). Stages: Closed Won/Swapped/Removed/Qualified Active/Negotiation/Proposal/etc.",
                "columns": (
                    "Id, Name, StageName, Amount, CloseDate, Probability, "
                    "AccountId, OwnerId, Type, IsClosed, IsWon"
                ),
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

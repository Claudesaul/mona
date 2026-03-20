"""Compact database schema descriptions for Claude system prompt.

Optimized for minimal token usage — only columns and notes that affect query correctness.
"""

SCHEMAS = {
    "snowflake": {
        "name": "Snowflake",
        "type": "Snowflake SQL",
        "description": "Revenue, sales, fulfillment, operational analytics. Fact tables join to dims via KEY columns. Date keys are serial ints — use TIMESTAMP columns for filtering. Data: Jan 2024–present.",
        "tables": {
            "RECOGNIZESALESREVENUEFACT_V": {
                "description": "Revenue per visit (29.6M rows). THE financial table.",
                "columns": "LOCATIONKEY, ITEMKEY, ROUTEKEY, CUSTOMERKEY, MACHINEKEY (all INT FK), VISITDATETIME (TIMESTAMP — filter dates here), SALETYPE ('Day'/'Visit'), QUANTITYSOLD, ACTUALSALESBASEPRICE, ACTUALSALESEXTENDEDTOTALREVENUE (revenue), ALLOCATEDSALESEXTENDEDGROSSMARGIN (margin), EXTENDEDCOST, DELIVEREDQUANTITY, NUMBERSPOILED, EXTENDEDSPOILEDVALUE, SERVICEBYUSERNAME (driver)",
                "joins": ["DIMLOCATION_V ON LOCATIONKEY", "DIMITEM_V ON ITEMKEY", "DIMROUTE_V ON ROUTEKEY"],
            },
            "MICROMARKETSALESFACT_V": {
                "description": "Micro market transactions (20.3M rows).",
                "columns": "LOCATIONKEY, ITEMKEY (FK), SALEDATETIME (TIMESTAMP — filter here), QUANTITY, EXTENDEDTOTALPRICE, PRODUCTCOST, PAR, CURRENTINVENTORY, WASOUTOFSTOCK, WASDEPLETED",
                "joins": ["DIMLOCATION_V ON LOCATIONKEY", "DIMITEM_V ON ITEMKEY"],
            },
            "ORDERTOFULFILLMENTVENDINGMARKETFACT_V": {
                "description": "Order-to-fulfillment (31.8M rows). No TIMESTAMP — convert datekeys: DATEADD(day, DELIVERYDATEKEY, '1899-12-31').",
                "columns": "LOCATIONKEY, ITEMKEY, MACHINEKEY (FK), TARGETDELIVERYDATEKEY, PICKDATEKEY, DELIVERYDATEKEY (serial ints), ORDERQUANTITY, PICKQUANTITY, DELIVEREDQUANTITY, SPOILQUANTITY, REMOVEQUANTITY, COILOOS, PAR, ITEMCOST, DELIVERYDRIVERNAME",
                "joins": ["DIMLOCATION_V ON LOCATIONKEY", "DIMITEM_V ON ITEMKEY"],
            },
            "SALESBYCOILFACT_V": {
                "description": "Sales by coil position (47.9M rows). No TIMESTAMP — use DATEADD(day, EXTRACTDATEKEY, '1899-12-31').",
                "columns": "LOCATIONKEY, ITEMKEY, MACHINEKEY (FK), EXTRACTDATEKEY (serial), PAR, ACTUALSALESTODAYVALUE, AVERAGEDAILYSALESVALUE, ACTUALVENDPRICEVALUE, INVENTORY",
                "joins": ["DIMLOCATION_V ON LOCATIONKEY", "DIMITEM_V ON ITEMKEY"],
            },
            "DIMITEM_V": {
                "description": "Items (6.4K). Use for lookups and joins.",
                "columns": "ITEMKEY (PK), NAME, CODE, CATEGORY, MANUFACTURER, UNITCOST, SHELFLIFE, CURRENTROWINDICATOR ('Current'=active), DELETED ('Active'/'Deleted')",
            },
            "DIMLOCATION_V": {
                "description": "Locations (1.7K). Use for lookups and joins.",
                "columns": "LOCATIONKEY (PK), NAME, CODE, ADDRESS1, CITY, STATE, ZIP, REGION, CHANNEL, LOCATIONTYPE, MANAGEMENTCOMPANYNAME, PRIMARYCONSUMERTYPE, GEOCODELATITUDE, GEOCODELONGITUDE, DELETED ('Active'/'Deleted')",
            },
            "DIMROUTE_V": {
                "description": "Routes (65).",
                "columns": "ROUTEKEY (PK), NAME, CODE, DRIVERNAME, DELETED",
            },
            "DIMCUSTOMER_V": {
                "description": "Customers (551).",
                "columns": "CUSTOMERKEY (PK), NAME, CITY, STATE, CUSTOMERGROUP, ACCOUNTMANAGERUSERNAME, SALESPERSONUSERNAME",
            },
            "WAREHOUSEINVENTORYFACT_V": {
                "description": "Warehouse inventory snapshots (8.3M rows).",
                "columns": "WAREHOUSEKEY, ITEMKEY (FK), INVENTORYDATEKEY (serial), INVENTORYTIME (TIMESTAMP), CURRENTPERPETUALINVENTORYEACHES (qty), CURRENTPERPETUALINVENTORYVALUE ($), PARLEVELEACHES",
            },
        },
    },
    "lightspeed": {
        "name": "LightSpeed",
        "type": "T-SQL",
        "description": "Orders and picks. NO price/cost/revenue. Data: Dec 2025–present.",
        "tables": {
            "dbo.ItemView": {
                "description": "Order line items (4.8M rows). NO financial data. Always filter by orderDate.",
                "columns": "id (order ID), locDescription (location), cusDescription (customer), rteDescription (route), orderDate, PickDate, completedTime, product (item name), productID, categoryID (category), quantity (ordered), updatedQuantity (picked), par, capacity, statusId (1=Queried 2=Queued 3=Picking 4=Picked 5=Printed 6=Filtered 7=Staged), SecondsToPick",
            },
            "dbo.OrderTotals": {
                "description": "Order-level summary.",
                "columns": "orderedQuantity, pickedQuantity, nolightQuantity, elapsedTotalSeconds",
            },
            "dbo.RouteTotals": {
                "description": "Route-level aggregates.",
                "columns": "totalPicked, noLightQuantity, orders, SnackTotes, XBINTotes, totalSeconds, startTime, endTime",
            },
        },
    },
    "level": {
        "name": "Level",
        "type": "T-SQL",
        "description": "Warehouse inventory, par levels, POs, receiving, vendors.",
        "tables": {
            "dbo.AreaItemParView": {
                "description": "Current inventory and pars (4.9K rows).",
                "columns": "itemID, itemName, itemCode, itemActive (BIT), FillTo (par), ReorderPoint, SafetyStock, currentQty, areaName (warehouse area), vendorName, DaysToFillTo, lastUpdate",
            },
            "dbo.QohByArea": {
                "description": "QOH by storage area (1.6K rows).",
                "columns": "StorageArea, itemID, ItemName, QOH, Category, ItemCode, FillTo",
            },
            "dbo.PurchaseOrder": {
                "description": "POs (26.7K rows). 2016–present.",
                "columns": "ID, vendorID (FK), voided, received, orderDate, expectedReceiptDate, Comments, Submitted",
            },
            "dbo.Vendor": {
                "description": "Vendors (178).",
                "columns": "id, Name, Code, active",
            },
            "dbo.ReceiptView": {
                "description": "Receiving history (273K rows).",
                "columns": "receiptID, vendorID, vendor (name), transactionDate, receiptDate, quantity (cases), extendedQuantity (eaches), product (item), itemID, cost (case), sizeCost (unit), storageArea, validated, voided",
            },
            "dbo.PoiView": {
                "description": "PO line items with velocity (557K rows).",
                "columns": "purchaseOrderID (FK), itemName, itemCode, quantity, expectedCost, extendedQuantity, itemQoh, itemFillTo, AvgVelocityItmBranch30Day, CurrentDaysSupply, DaysOnOrder",
            },
        },
    },
    "oos": {
        "name": "OOS",
        "type": "PostgreSQL",
        "description": "Fill rates, OOS, product activity. ONLY Market locations. Column names in views use Title Case — double-quote them. Data: Nov 2025–present.",
        "tables": {
            "oos_details_by_date": {
                "description": "Coil-level readings (12.5M rows). MUST filter by date.",
                "columns": 'location, route, item, item_category, item_code, price, par, current_level (0=OOS), date (TIMESTAMP)',
                "notes": ["ALWAYS filter by date."],
            },
            "product_activity": {
                "description": "Rolling 14-day movement (152K rows). NO date column.",
                "columns": "location, item, item_code, item_category, added_qty, sold_qty, shrink_qty, shrink_cost, spoiled_qty, spoiled_cost, removed_qty, market_price",
                "notes": ["NO date column — never filter by date."],
            },
            "v_daily_oos": {
                "description": "Today's OOS by location (523 rows).",
                "columns": '"Location", "Route", "Fill" (0-1), "OOS" (count), "Note"',
            },
            "v_daily_oos_details": {
                "description": "Today's OOS coils with demand (1K rows).",
                "columns": '"Location", "Asset ID", "Coil", "Item Code", "Item", "Par", "Sold Qty", "Spoiled Qty", "Shrink Qty", "Demand/Day", "DaysOnHand"',
            },
            "v_weekly_oos": {
                "description": "Weekly OOS by location (3K rows).",
                "columns": '"Location", "Week" (text like \'08-Mar\'), "OOS"',
            },
            "v_future_daily_oos": {
                "description": "Predicted shorts (485 rows).",
                "columns": '"LOC", "shorts"',
            },
            "v_this_week_oos_details": {
                "description": "This week's OOS details (5.9K rows).",
                "columns": '"Location", "Asset ID", "Coil", "Item Code", "Item", "Item Category", "Par", "Curr_Lvl", "Date"',
            },
            "v_last_week_oos_details": {
                "description": "Last week's OOS details (6.2K rows).",
                "columns": '"Location", "Asset ID", "Route", "Coil", "Item Code", "Item", "Item Category", "Par", "Curr_Lvl", "Date"',
            },
            "v_weekly_oos_pivot": {
                "description": "Weekly OOS pivot (526 rows).",
                "columns": '"Location", 6 week columns, "Total"',
            },
        },
    },
    "salesforce": {
        "name": "Salesforce",
        "type": "SOQL",
        "description": "CRM — accounts, contacts, tasks, cases, opportunities.",
        "tables": {
            "Account": {
                "description": "Accounts (2,092 — customers + prospects).",
                "columns": "Id, Name, Type (Customer/Prospect/Partner), BillingCity, BillingState, Industry, Phone, Website, OwnerId",
            },
            "Contact": {
                "description": "Contacts (5.4K).",
                "columns": "Id, FirstName, LastName, Name, Email, Phone, Title, Department, AccountId (FK)",
            },
            "Task": {
                "description": "Tasks (12.4K). Status: Open/Completed/In Progress/On Hold.",
                "columns": "Id, Subject, Status, Priority, ActivityDate, Description, AccountId, OwnerId, IsClosed",
            },
            "Case": {
                "description": "Cases (44K). Mostly equipment installs/removals.",
                "columns": "Id, CaseNumber, Subject, Status, Priority, Type, AccountId, ContactId, CreatedDate, ClosedDate, IsClosed",
            },
            "Opportunity": {
                "description": "Opportunities (4K).",
                "columns": "Id, Name, StageName, Amount, CloseDate, Probability, AccountId, OwnerId, IsClosed, IsWon",
            },
        },
    },
    "sharepoint": {
        "name": "SharePoint Files",
        "type": "File Search",
        "description": "Shared drive files synced via OneDrive. ~9,100 files across 3 document libraries. Search by filename keyword, folder, file type, modified date. Returns metadata + download links (not file contents).",
        "tables": {
            "Business Intelligence - Documents": {
                "description": "Main BI library. Subfolders: Reporting (Daily, Weekly, Monthly, Ad Hoc, Scorecard), Merchandising, Pricing, OCS to Seed, Processes, Cases.",
                "columns": "xlsx (5,738), xlsm (1,587), csv (190), docx (282), pdf (214), pptx (20)",
            },
            "Customer Operations - Documents": {
                "description": "Customer operations documentation and resources.",
                "columns": "Mixed file types",
            },
            "Standards & Process - Documents": {
                "description": "SOPs, standards, process documentation.",
                "columns": "Mixed file types",
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

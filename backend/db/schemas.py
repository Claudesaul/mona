"""Database schema descriptions for Claude system prompt injection.

These descriptions help Claude understand the available tables, columns, and
relationships so it can write accurate SQL queries.
"""

SCHEMAS = {
    "lightspeed": {
        "name": "LightSpeed",
        "type": "SQL Server",
        "description": "Order and transaction data for Monumental Markets vending and micro-market operations.",
        "tables": {
            "dbo.ItemView": {
                "description": (
                    "Primary order/transaction view (~4.7M rows). Contains all item-level order data "
                    "including what was ordered, where, when, and fulfillment status."
                ),
                "columns": {
                    "id": "INT - Unique order line item ID",
                    "locID": "INT - Location ID",
                    "locDescription": "NVARCHAR - Location name/description (e.g., 'Washington Hospital Center')",
                    "machineBarcode": "NVARCHAR - Machine/asset barcode identifier",
                    "orderDate": "DATETIME - Date the order was placed",
                    "product": "NVARCHAR - Product name/description",
                    "quantity": "INT - Originally ordered quantity",
                    "updatedQuantity": "INT - Final/adjusted quantity (after modifications)",
                    "coil": "NVARCHAR - Coil/slot position in the machine",
                    "statusId": "INT - Order status (1=Open, 2=Processed, 3=Shipped, 4=Delivered, 5=Cancelled)",
                    "providerName": "NVARCHAR - Supplier/provider name",
                    "rteID": "INT - Route ID",
                    "rteDescription": "NVARCHAR - Route name/description (e.g., 'Route 1 - Downtown')",
                    "categoryDescription": "NVARCHAR - Product category",
                    "upc": "NVARCHAR - Universal Product Code",
                    "itemID": "INT - Internal item/product ID",
                    "parLevel": "INT - Par level for the coil position",
                    "machineDescription": "NVARCHAR - Machine/asset description",
                    "lastDeliveryDate": "DATETIME - Date of most recent delivery",
                    "scheduledDeliveryDate": "DATETIME - Next scheduled delivery date",
                },
                "notes": [
                    "This is a VIEW, not a base table. Use SELECT only.",
                    "orderDate is the most common filter column.",
                    "Use locDescription for location name searches.",
                    "statusId=5 means cancelled - typically exclude these.",
                    "updatedQuantity reflects the actual delivered quantity.",
                ],
            },
        },
    },
    "level": {
        "name": "Level",
        "type": "SQL Server",
        "description": "Inventory, warehouse, and purchasing data for Monumental Markets.",
        "tables": {
            "dbo.AreaItemParView": {
                "description": (
                    "Inventory par level view showing target stock levels by area/location. "
                    "Used for inventory management and replenishment planning."
                ),
                "columns": {
                    "AreaId": "INT - Area/location ID",
                    "AreaName": "NVARCHAR - Area/location name",
                    "ItemId": "INT - Item ID",
                    "ItemName": "NVARCHAR - Item/product name",
                    "ParLevel": "INT - Target par level (desired stock quantity)",
                    "UPC": "NVARCHAR - Universal Product Code",
                    "CategoryName": "NVARCHAR - Product category name",
                    "VendorName": "NVARCHAR - Vendor/supplier name",
                },
            },
            "dbo.PurchaseOrder": {
                "description": "Purchase orders placed with vendors.",
                "columns": {
                    "PurchaseOrderId": "INT - Primary key",
                    "VendorId": "INT - Vendor ID (FK to Vendor)",
                    "OrderDate": "DATETIME - Date order was placed",
                    "ExpectedDate": "DATETIME - Expected delivery date",
                    "Status": "INT - Order status",
                    "TotalAmount": "DECIMAL - Total order amount",
                    "Notes": "NVARCHAR - Order notes",
                },
            },
            "dbo.PurchaseOrderItem": {
                "description": "Line items within purchase orders.",
                "columns": {
                    "PurchaseOrderItemId": "INT - Primary key",
                    "PurchaseOrderId": "INT - FK to PurchaseOrder",
                    "ItemId": "INT - FK to Item",
                    "Quantity": "INT - Ordered quantity",
                    "UnitCost": "DECIMAL - Cost per unit",
                    "ReceivedQuantity": "INT - Actually received quantity",
                },
            },
            "dbo.Item": {
                "description": "Master item/product catalog.",
                "columns": {
                    "ItemId": "INT - Primary key",
                    "ItemName": "NVARCHAR - Product name",
                    "UPC": "NVARCHAR - Universal Product Code",
                    "CategoryId": "INT - FK to category",
                    "VendorId": "INT - FK to vendor",
                    "IsActive": "BIT - Whether item is active",
                },
            },
            "dbo.ItemSize": {
                "description": "Item size/packaging variants.",
                "columns": {
                    "ItemSizeId": "INT - Primary key",
                    "ItemId": "INT - FK to Item",
                    "SizeName": "NVARCHAR - Size description",
                    "UPC": "NVARCHAR - UPC for this size variant",
                },
            },
            "dbo.Vendor": {
                "description": "Vendor/supplier master data.",
                "columns": {
                    "VendorId": "INT - Primary key",
                    "VendorName": "NVARCHAR - Vendor company name",
                    "ContactName": "NVARCHAR - Primary contact",
                    "Phone": "NVARCHAR - Phone number",
                    "Email": "NVARCHAR - Email address",
                },
            },
        },
    },
    "oos": {
        "name": "OOS (Out-of-Stock)",
        "type": "PostgreSQL",
        "description": (
            "Out-of-stock tracking database for Monumental Markets. Tracks daily stock levels, "
            "OOS percentages, and product movement across all vending/micro-market locations."
        ),
        "tables": {
            "oos_details_by_date": {
                "description": (
                    "Main OOS tracking table (~12M rows). One row per coil position per day, "
                    "showing stock levels and OOS status."
                ),
                "columns": {
                    "location": "TEXT - Location name",
                    "route": "TEXT - Route name/description",
                    "asset_id": "TEXT - Machine/asset identifier",
                    "asset_type": "TEXT - Type of asset (e.g., 'Vending', 'Micro Market')",
                    "coil": "TEXT - Coil/slot position",
                    "shelf": "TEXT - Shelf position",
                    "position": "TEXT - Position on shelf",
                    "item_category": "TEXT - Product category",
                    "item_code": "TEXT - Product code/SKU",
                    "item": "TEXT - Product name",
                    "price": "NUMERIC - Item retail price",
                    "par": "INTEGER - Par level (target stock)",
                    "current_level": "INTEGER - Current stock level",
                    "date": "DATE - Date of the reading",
                },
                "notes": [
                    "Extremely large table. ALWAYS filter by date.",
                    "current_level = 0 means the coil is out of stock.",
                    "OOS percentage = COUNT(current_level=0) / COUNT(*) for a location/date.",
                    "Use date ranges to limit results. Never query without a date filter.",
                ],
            },
            "product_activity": {
                "description": (
                    "Rolling ~14-day snapshot of product movement. Shows quantities added, sold, "
                    "shrunk, spoiled, and removed per product per location. NO date column — the "
                    "table only contains the most recent ~14 days of activity as a whole."
                ),
                "columns": {
                    "location": "TEXT - Location name",
                    "item": "TEXT - Product name",
                    "item_code": "TEXT - Product code/SKU",
                    "item_category": "TEXT - Product category",
                    "added_qty": "INTEGER - Quantity added/stocked",
                    "sold_qty": "INTEGER - Quantity sold",
                    "shrink_qty": "INTEGER - Quantity lost to shrinkage",
                    "spoiled_qty": "INTEGER - Quantity spoiled/expired",
                    "removed_qty": "INTEGER - Quantity removed",
                    "market_price": "NUMERIC - Retail price",
                },
                "notes": [
                    "NO date column. Do NOT try to filter by date. The entire table is recent data (~14 days).",
                    "Use for sales velocity, shrinkage analysis, and identifying slow/fast movers.",
                ],
            },
            "v_daily_oos": {
                "description": "View: Daily OOS summary by location with OOS percentage.",
                "columns": {
                    "location": "TEXT - Location name",
                    "route": "TEXT - Route name",
                    "date": "DATE - Date",
                    "total_coils": "BIGINT - Total coil positions",
                    "oos_coils": "BIGINT - Number of empty coils",
                    "oos_percentage": "NUMERIC - OOS rate as percentage",
                },
            },
            "v_weekly_oos": {
                "description": "View: Weekly OOS summary by location.",
                "columns": {
                    "location": "TEXT - Location name",
                    "route": "TEXT - Route name",
                    "week_start": "DATE - Start of the week",
                    "avg_oos_percentage": "NUMERIC - Average OOS rate for the week",
                },
            },
            "v_daily_oos_details": {
                "description": "View: Detailed daily OOS at the coil level (items that are out of stock).",
                "columns": {
                    "location": "TEXT - Location name",
                    "route": "TEXT - Route name",
                    "asset_id": "TEXT - Machine/asset identifier",
                    "coil": "TEXT - Coil position",
                    "item": "TEXT - Product name that should be in this coil",
                    "par": "INTEGER - Target stock level",
                    "date": "DATE - Date",
                },
            },
        },
    },
    "salesforce": {
        "name": "Salesforce",
        "type": "SOQL",
        "description": "CRM data — customer accounts, contacts, tasks, events, cases, opportunities, leads.",
        "tables": {
            "Account": {
                "description": "Customer accounts (~2K records). Each account represents a customer location or company.",
                "columns": {
                    "Id": "ID - Unique account ID",
                    "Name": "STRING - Account/company name",
                    "Type": "PICKLIST - Account type",
                    "BillingCity": "STRING - City",
                    "BillingState": "STRING - State",
                    "Industry": "PICKLIST - Industry type",
                    "OwnerId": "REFERENCE - Account owner (user ID)",
                    "CreatedDate": "DATETIME - When account was created",
                    "LastModifiedDate": "DATETIME - Last updated",
                },
            },
            "Contact": {
                "description": "People associated with accounts (~5K records).",
                "columns": {
                    "Id": "ID - Unique contact ID",
                    "Name": "STRING - Full name",
                    "Email": "STRING - Email address",
                    "Phone": "STRING - Phone number",
                    "Title": "STRING - Job title",
                    "AccountId": "REFERENCE - Parent account ID",
                },
                "notes": ["Use Account.Name to get the account name in queries."],
            },
            "Task": {
                "description": "Tasks and activities (~12K records).",
                "columns": {
                    "Id": "ID - Unique task ID",
                    "Subject": "STRING - Task subject/title",
                    "Status": "PICKLIST - Status (e.g., Completed, Not Started)",
                    "Priority": "PICKLIST - Priority level",
                    "ActivityDate": "DATE - Due date",
                    "Description": "TEXT - Task details",
                    "AccountId": "REFERENCE - Related account",
                    "OwnerId": "REFERENCE - Assigned user",
                    "IsClosed": "BOOLEAN - Whether task is complete",
                    "CreatedDate": "DATETIME - When created",
                },
            },
            "Case": {
                "description": "Support cases and issues (~43K records).",
                "columns": {
                    "Id": "ID - Unique case ID",
                    "Subject": "STRING - Case subject",
                    "Status": "PICKLIST - Status",
                    "Priority": "PICKLIST - Priority",
                    "AccountId": "REFERENCE - Related account",
                    "ContactId": "REFERENCE - Related contact",
                    "CreatedDate": "DATETIME - When opened",
                    "ClosedDate": "DATETIME - When resolved",
                },
            },
            "Opportunity": {
                "description": "Sales opportunities (~4K records).",
                "columns": {
                    "Id": "ID - Unique opportunity ID",
                    "Name": "STRING - Opportunity name",
                    "StageName": "PICKLIST - Sales stage",
                    "Amount": "CURRENCY - Deal amount",
                    "CloseDate": "DATE - Expected close date",
                    "AccountId": "REFERENCE - Related account",
                    "OwnerId": "REFERENCE - Opportunity owner",
                },
            },
        },
    },
}


def get_schema_description() -> str:
    """Generate a formatted schema description string for the Claude system prompt."""
    lines = []

    for db_key, db_info in SCHEMAS.items():
        lines.append(f"\n### {db_info['name']} Database ({db_info['type']})")
        lines.append(db_info["description"])

        for table_name, table_info in db_info["tables"].items():
            lines.append(f"\n**{table_name}**: {table_info['description']}")
            lines.append("Columns:")

            for col_name, col_desc in table_info["columns"].items():
                lines.append(f"  - {col_name}: {col_desc}")

            if "notes" in table_info:
                lines.append("Notes:")
                for note in table_info["notes"]:
                    lines.append(f"  * {note}")

    return "\n".join(lines)

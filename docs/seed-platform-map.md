# Seed (Cantaloupe) Platform Map

Explored 2026-03-20 via Playwright browser automation.
Login: mycantaloupe.com → Cluster: cs2
URL pattern: `https://mycantaloupe.com/cs2/Dist/index.html/frame/{PageName}`

## Dashboard (Home)

The main landing page shows live operational cards:

| Card | Data |
|------|------|
| **Summary** | 688 Locations, 177/260 Serviced, 43 Routes, 11/38 Completed |
| **Monthly Sales** | Bar chart (Jan–Mar 2026), revenue by month |
| **No Sales** | Vending: 0, Markets: 0 |
| **No Contact** | Vending: 3, Markets: 28 |
| **Price Exceptions** | Current: 0, RPC Sent: 0 |
| **Restocks** | Serviced 743/996, Scheduled 1071/1004, Missing Inventories 4/1, Missing Services 325/7, Unscheduled 27/59 |
| **Warehouse** | Out of Stock: 1555, Bad Inventory: 1554 |
| **Live Data** | Map with serviced/scheduled location pins |

## Sidebar Sections

### Alerts (all loaded via classic frame URLs)

| Page | URL Path | Rows | Columns/Content |
|------|----------|------|-----------------|
| Service Ticket Dispatch | `ServiceTicketDispatch` | 8 | Technicians: Anthony Russell, Ilya Umansky |
| New Service Ticket | `ServiceTicketEdit` | 15 | Ticket creation form |
| Machine Alerts | `MachineAlerts` | 165 | Out of Order Machines — "Missing Products" by location |
| DEX Alerts | `DexAlerts` | — | Empty |
| Inventory Alerts | `InventoryAlerts` | 158 | Negative/bad inventory items by location + asset |
| Sales Alerts | `SalesAlerts` | — | Empty (no locations with zero sales) |
| Bill & Coin Alerts | `BillAndCoinAlerts` | — | Empty |
| Coil Alerts | `CoilAlerts` | — | Empty |
| Signal Alerts | `SignalStrengthAlerts` | 31 | Asset ID, Device, Location, Place, Type, Last Signal, Signal History |
| Cashless Alerts | `CashlessAlerts2` | 14 | Asset ID, SN, Location, Place, Type |

### Machine

| Page | URL Path | Rows | Columns/Content |
|------|----------|------|-----------------|
| Machine List | `/machine-list` (modern layout) | 249 | Filters: Status, Branch, Route. Actions: Import/Export, Seed Live, Show on Map |
| Machine Alerts | `MachineAlerts` | 165 | Out of order machines with missing product counts |
| Sales Summary | Requires machine selected | — | Per-machine sales detail |
| Monthly Sales | Requires machine selected | — | Per-machine monthly breakdown |
| Coil Summary | Requires machine selected | — | Per-machine coil-level data |
| Inventory Summary | Requires machine selected | — | Per-machine inventory snapshot |

### Delivery

| Page | URL Path | Rows | Columns/Content |
|------|----------|------|-----------------|
| Delivery Orders | `DeliveryOrderList` | 161 | Order, Branch, Route, Asset ID, Customer, Location/Place, Schedule Date, Created, Created By, Amount, Sun–Sat |
| Delivery Invoices | `DeliveryInvoiceList` | 160 | Invoice, Branch, Route, Asset ID, Customer, Created By, Schedule Date, Delivery Date, Invoice Date, Status, Sent, Amount, Sun–Thu |

### Scheduling

| Page | URL Path | Rows | Content |
|------|----------|------|---------|
| Routes Summary | `Scheduling/RoutesSummary` | 31 | "Easier Scheduling" — calendar view with routes, location counts, serviced/exceptions/locked status by date |

### Cash

| Page | URL Path | Rows | Columns/Content |
|------|----------|------|-----------------|
| Cash Ticket List | `CashTicketList` | 10 | Cash collection tickets by day-of-week (Sun–Sat) |
| Cash History | `CashHistory` | 6 | Asset ID, Serial Number, Location/Place, Type, Dex +/-, Meter +/-, Product +/- |
| Cash Input | `CashInput` | 10 | Cash input by day-of-week (Sun–Sat) |

### Warehouse

| Page | URL Path | Rows | Columns/Content |
|------|----------|------|-----------------|
| Warehouse Inventory | `WarehouseInventory` | 10 | Product, Case, Box, Each, Custom |

### Setup

| Page | URL Path | Rows | Content |
|------|----------|------|---------|
| Item Import Export | `ItemImportExport` | 129 | "Import Items" — Column to Export table, used by Monumator for product list downloads |

### Sections using modern layout (hash routes, not classic frame URLs)

These sections exist in the sidebar but use Angular/React routing (`#/section/page`), not classic iframe URLs. The exact routes were not discovered:

- **Finance** — Invoices, Invoice Summary, Commission Summary
- **Market** — Kiosk List, Market Sales, Market Inventory
- **Pricing** — Pricing Plan List, Commission Plan List
- **Cashless** — Cashless Summary, Cashless Transactions
- **Reports** — Spotlight Reports, Spotlight API, Custom Reports

## Seed Report API

The Seed Report API is separate from the web UI:

- **Endpoint**: `https://api.mycantaloupe.com/Reports/Run?ReportId={id}`
- **Auth**: Basic auth with SEED_USERNAME/SEED_PASSWORD
- **Returns**: Excel (.xlsx) file

Known report IDs (from Monumator config):

| Report | ID | Description |
|--------|-----|-------------|
| Daily Fill & OOS (POG) | 34608 | Planogram data → feeds OOS PostgreSQL `oos_details_by_date` |
| Product Activity | 32081 | 14-day product movement → feeds OOS PostgreSQL `product_activity` |
| Daily Fill & OOS | 33105 | Legacy fill/OOS report |
| Inventory Adjustment | 33110 | Previous day inventory changes (spoils, shrink, adds) |
| Delivery Point Invoice Details | 33636 | Invoice details for OCS budget |

Date filtering: append `&filter0={start_date}&filter0={end_date}` (YYYY-MM-DD format).

## Data Flow Summary

```
Seed (Cantaloupe) Platform
    │
    ├── Snowflake DW (PRD_SEED_DW_VIEW_SHARE_V1)
    │   └── Midnight daily dump → 44 views (sales, fulfillment, inventory, etc.)
    │   └── Queried by Mona via ODBC
    │
    ├── Seed Report API (api.mycantaloupe.com)
    │   └── On-demand Excel report downloads
    │   └── Used by Monumator to populate:
    │       ├── OOS PostgreSQL (oos_details_by_date, product_activity)
    │       └── SQLite backup + Access DB
    │
    ├── Seed Web UI (mycantaloupe.com)
    │   └── Live operational data (machines, scheduling, alerts)
    │   └── Not directly queried by Mona
    │
    └── LightSpeed + Level (separate systems)
        └── Order/pick tracking + warehouse inventory
        └── Queried by Mona via SQL Server ODBC
```

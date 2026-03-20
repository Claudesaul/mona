# Mona Dashboard Vision

## Overview

A real-time KPI dashboard that gives leadership (CFO, CEO, ops managers) an at-a-glance view of business health — powered by the same databases Mona already queries. The dashboard is NOT a replacement for chat — it's a companion. Users see the numbers at a glance, then drill into Mona's chat for the "why" behind any metric.

## Core Concept

**The dashboard answers the questions your team asks every single day, automatically.**

Instead of typing "what was revenue yesterday?" or "which locations have the worst fill rate?" every morning, the dashboard shows these answers live, refreshing on an interval. When something looks off, a single click opens Mona's chat pre-loaded with a drill-down question.

## Layout

### Top Bar
- Page title: "Mona Dashboard"
- Last refreshed timestamp with auto-refresh indicator (e.g., "Updated 2 min ago")
- Manual refresh button
- Date range selector (Today / This Week / This Month / Custom)
- Link back to Chat

### Hero KPI Cards (top row, always visible)
Large animated number cards with trend indicators. These are the 4-6 metrics leadership checks first:

| Card | Source | Query |
|------|--------|-------|
| **Today's Revenue** | Snowflake | `SUM(ACTUALSALESEXTENDEDTOTALREVENUE)` for today |
| **Avg Fill Rate** | OOS | `AVG("Fill")` from v_daily_oos |
| **Orders In Progress** | LightSpeed | Count of orders by statusId (Queued/Picking/Picked) |
| **OOS Count** | OOS | `SUM("OOS")` from v_daily_oos |
| **Gross Margin %** | Snowflake | margin / revenue * 100 |
| **Warehouse Alerts** | Level | Items below reorder point count |

Each card shows:
- Large number (animated count-up on load via Framer Motion)
- Trend arrow (up/down vs. same period last week/month)
- Sparkline or mini bar chart (last 7 days)
- Subtle color coding: green = good, amber = watch, red = attention needed

### Sections (scrollable below hero cards)

#### 1. Revenue & Sales
- Bar chart: Revenue by day (last 14 days)
- Horizontal bar: Top 10 locations by revenue this week
- Donut chart: Revenue by product category
- Table: Top/bottom performers (locations with biggest revenue change vs. prior period)

#### 2. Operations & Fill Rate
- Line chart: Fill rate trend (daily, last 30 days)
- Heat map or ranked list: Locations by fill rate (worst at top, color-coded)
- Bar chart: OOS count by route
- Table: Top OOS items (most frequently out of stock)

#### 3. Order & Fulfillment
- Stacked bar: Orders by status (Queried/Queued/Picking/Picked/Staged)
- Timeline: Average pick time by route
- Table: Today's orders with completion %

#### 4. Warehouse & Inventory
- Gauge charts: Overall warehouse fill level
- Alert list: Items below reorder point (sorted by urgency)
- Bar chart: Days of supply distribution

#### 5. Product Health
- Scatter plot: Items by sell-through rate vs. spoilage cost
- Table: Top spoilage items (14-day rolling)
- Table: Top shrinkage items

### Each Section Has:
- Collapsible/expandable cards
- Horizontal scroll for overflow tables on mobile
- "Ask Mona" button on every card — clicks pre-loads a relevant question into the chat

## Mona AI Integration

### "Mona's Take" Button
A prominent button (or floating action button) that, when clicked, triggers Mona to analyze the current dashboard state and produce a brief executive summary:

> "Revenue is up 3.2% vs. last week, driven by strong performance at Pentagon City and Tysons. However, fill rates at 3 locations dropped below 80% — Capitol Hill, Navy Yard, and L'Enfant Plaza are showing increased OOS in the Beverage category. Spoilage at the warehouse is trending up on fresh food items. I'd recommend reviewing the par levels for HK/MG items at those low-fill locations."

This summary would:
1. Highlight what's going well
2. Flag areas needing attention
3. Suggest specific actions
4. Reference actual numbers from the dashboard queries

### Drill-Down Chat
Every metric, chart, and table row should be clickable with an "Ask Mona" action that opens the chat with a pre-filled question:
- Click on a location's revenue number -> "Break down revenue at [Location] by category this week"
- Click on a low fill rate -> "Why is fill rate low at [Location]? Show me the OOS items"
- Click on a spoilage number -> "What items have the highest spoilage at [Location]?"

## Technical Approach

### Data Flow
```
Dashboard Page (React)
  -> fetches /api/dashboard/kpis on interval (every 5 min)
  -> Backend runs predefined queries against existing databases
  -> Returns structured JSON for each KPI section
  -> Frontend renders with charts + animations
```

### Backend: New Dashboard Module
- `backend/dashboard.py` — predefined queries for each KPI card/section
- `GET /api/dashboard/kpis` — returns all dashboard data in one payload
- `GET /api/dashboard/section/{name}` — returns data for a specific section (lazy loading)
- Queries are cached aggressively (5-10 min TTL) since dashboard data doesn't need to be real-time
- Reuses ALL existing database connections from `db/connections.py`

### Frontend: New Dashboard Page
- `frontend/src/components/DashboardPage.tsx` — main dashboard layout
- `frontend/src/components/dashboard/` — sub-components for each section
- Chart library: **Recharts** (React-native, works with Framer Motion, lightweight)
- Animations: Framer Motion for card entrances, number count-ups, chart transitions
- Responsive: Cards stack vertically on mobile, grid on desktop
- Auto-refresh: `useEffect` with `setInterval` polling `/api/dashboard/kpis`

### Routing
- Add `/dashboard` route to `App.tsx` (alongside existing `/`, `/explore`, `/about`)
- Add "Dashboard" link to the Header nav

## Design Language

### Colors
- **Green** (#10b981 / emerald): healthy metrics, positive trends
- **Amber** (#f59e0b): metrics that need watching
- **Red** (#ef4444): metrics that need immediate attention
- Thresholds are configurable per metric (e.g., fill rate < 85% = amber, < 75% = red)

### Animations (Framer Motion)
- Cards fade + slide in on load (staggered, 50ms apart)
- Numbers count up from 0 to final value (500ms, ease-out)
- Trend arrows bounce in
- Charts draw themselves (line charts trace, bars grow up)
- Refresh: cards pulse briefly when data updates
- Page transitions: smooth cross-fade from chat to dashboard

### Dark/Light Mode
- Respects existing theme toggle
- Charts adapt colors to theme
- Cards use the same glass-morphism style as chat bubbles

## Example KPI Queries (reuse existing database logic)

```sql
-- Today's Revenue (Snowflake)
SELECT ROUND(SUM(ACTUALSALESEXTENDEDTOTALREVENUE), 2) AS revenue,
       ROUND(SUM(ALLOCATEDSALESEXTENDEDGROSSMARGIN), 2) AS margin
FROM RECOGNIZESALESREVENUEFACT_V
WHERE VISITDATETIME >= CURRENT_DATE

-- Fill Rate (OOS PostgreSQL)
SELECT ROUND(AVG("Fill") * 100, 1) AS avg_fill,
       SUM("OOS") AS total_oos,
       COUNT(*) AS location_count
FROM v_daily_oos

-- Order Status (LightSpeed)
SELECT statusId,
       CASE statusId WHEN 1 THEN 'Queried' WHEN 2 THEN 'Queued'
            WHEN 3 THEN 'Picking' WHEN 4 THEN 'Picked'
            WHEN 5 THEN 'Printed' WHEN 7 THEN 'Staged' END AS status,
       COUNT(DISTINCT id) AS orders,
       SUM(quantity) AS items
FROM dbo.ItemView
WHERE orderDate >= CAST(GETDATE() AS DATE)
GROUP BY statusId

-- Warehouse Alerts (Level)
SELECT COUNT(*) AS below_reorder
FROM dbo.AreaItemParView
WHERE itemActive = 1 AND currentQty < ReorderPoint AND ReorderPoint > 0

-- Revenue Trend (Snowflake, last 14 days)
SELECT CAST(VISITDATETIME AS DATE) AS day,
       ROUND(SUM(ACTUALSALESEXTENDEDTOTALREVENUE), 2) AS revenue
FROM RECOGNIZESALESREVENUEFACT_V
WHERE VISITDATETIME >= DATEADD(day, -14, CURRENT_DATE)
GROUP BY CAST(VISITDATETIME AS DATE)
ORDER BY day

-- Top Spoilage (OOS product_activity)
SELECT item, item_category, location,
       spoiled_qty, spoiled_cost
FROM product_activity
WHERE spoiled_qty > 0
  AND item_category NOT IN ('Equipment Rental', 'Fee')
  AND item NOT LIKE 'HK %' AND item NOT LIKE 'MG %' AND item NOT LIKE 'YS %'
ORDER BY spoiled_cost DESC
LIMIT 15
```

## Implementation Phases

### Phase 1: Foundation
- Backend: `/api/dashboard/kpis` endpoint with hero card queries
- Frontend: Dashboard page with 4-6 hero KPI cards
- Auto-refresh on interval
- Navigation link in header

### Phase 2: Sections
- Add the 5 sections with charts (Recharts)
- Lazy-load sections as user scrolls
- "Ask Mona" buttons on each card

### Phase 3: AI Analysis
- "Mona's Take" button — sends dashboard data to Claude for executive summary
- Drill-down chat integration (click metric -> pre-filled chat question)

### Phase 4: Polish
- Sparklines on hero cards
- Trend comparisons (vs. last week/month)
- Configurable thresholds (admin can set what's green/amber/red)
- Mobile-optimized layout

## Why This Matters

The dashboard turns Mona from a "question answering tool" into a **business intelligence platform**. Your CFO doesn't need to type questions to see if revenue is on track — they open the dashboard and know in 2 seconds. When they need to dig deeper, Mona is one click away. This is the difference between a useful tool and an indispensable one.

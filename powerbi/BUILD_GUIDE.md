# Power BI dashboard: step-by-step build guide

This guide builds a 2-page interactive dashboard from `data/clean/sales_clean.csv`.
Time needed: about 1.5–2 hours the first time.

## 1. Import the data

1. Open **Power BI Desktop** → **Get data → Text/CSV** → choose `data/clean/sales_clean.csv`.
2. Click **Transform Data** (Power Query) and check data types:
   - `order_date`, `ship_date` → **Date**
   - `quantity`, `shipping_days`, `order_year`, `order_month` → **Whole number**
   - `unit_price`, `discount`, `sales`, `cost`, `profit`, `profit_margin` → **Decimal number**
3. **Close & Apply**.

## 2. Create a Calendar table

**Modeling → New table**:

```DAX
Calendar =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2023, 1, 1 ), DATE ( 2024, 12, 31 ) ),
    "Year", YEAR ( [Date] ),
    "Month No", MONTH ( [Date] ),
    "Month", FORMAT ( [Date], "MMM" ),
    "Year-Month", FORMAT ( [Date], "YYYY-MM" ),
    "Quarter", "Q" & QUARTER ( [Date] )
)
```

- Select the `Month` column → **Sort by column → Month No**.
- **Model view**: drag `Calendar[Date]` onto `sales_clean[order_date]` to create the relationship (one-to-many).
- Right-click `Calendar` → **Mark as date table** → choose `Date`.

## 3. Add the measures

Create every measure from [DAX_MEASURES.md](DAX_MEASURES.md). Keep them in one place: **Home → Enter data** → create an empty table called `_Measures`, then move each measure into it (select measure → **Home table** → `_Measures`).

## 4. Page 1: Sales Overview

| Area | Visual | Fields |
|---|---|---|
| Top row | 5 **Card** visuals | Total Sales, Total Profit, Profit Margin %, Total Orders, Sales YoY % |
| Middle left | **Line chart** | X: Calendar[Month], Y: Total Sales, Legend: Calendar[Year] |
| Middle right | **Clustered bar chart** | Y: category, X: Total Sales and Total Profit |
| Bottom left | **Map** or **Filled map** | Location: state, Bubble size: Total Sales |
| Bottom right | **Donut chart** | Legend: segment, Values: Total Sales |
| Left side | **Slicers** | Calendar[Year], region, category |

## 5. Page 2: Profit Deep Dive

| Area | Visual | Fields |
|---|---|---|
| Top | **Column chart** | X: Discount Band, Y: Profit Margin % (shows how discounts hurt profit) |
| Middle left | **Matrix** | Rows: category → sub_category, Values: Total Sales, Total Profit, Profit Margin % |
| Middle right | **Table** | Top 10 products by Total Profit (use visual filter: Top N = 10) |
| Bottom | **Line and clustered column chart** | X: Calendar[Year-Month], Columns: Total Sales, Line: Sales 3M Rolling Avg |

Add **conditional formatting** on Profit Margin % in the matrix: **Background color → Rules** (red below 0, green above 0.2).

## 6. Make it interactive

- **Format → Edit interactions** so slicers filter every visual.
- Add a **drill-through** page for `category` (right-click a category → see its sub-categories and products).
- Add a **tooltip page** showing Sales MoM % when hovering on the line chart.

## 7. Design tips

- One colour for sales, one for profit, red only for losses.
- Title every visual as a question or finding, for example *"Electronics drives 65% of sales"*.
- Align visuals to a grid (**View → Gridlines** and **Snap to grid**).

## 8. Save and publish screenshots

1. Save as `powerbi/Sales_Trend_Analyzer.pbix`.
2. Take a screenshot of each page and save them as `powerbi/screenshots/page1_overview.png` and `powerbi/screenshots/page2_profit.png`.
3. Add the screenshots to the README (the README already has the image links ready).

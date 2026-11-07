# DAX measures

Create these in Power BI Desktop: **Home → New measure**. The table is called `sales_clean` (the name Power BI gives the imported CSV). A `Calendar` date table is used for time intelligence. See [BUILD_GUIDE.md](BUILD_GUIDE.md) for how to create it.

## Core KPIs

```DAX
Total Sales = SUM ( sales_clean[sales] )

Total Profit = SUM ( sales_clean[profit] )

Profit Margin % = DIVIDE ( [Total Profit], [Total Sales] )

Total Orders = DISTINCTCOUNT ( sales_clean[order_id] )

Total Customers = DISTINCTCOUNT ( sales_clean[customer_id] )

Avg Order Value = DIVIDE ( [Total Sales], [Total Orders] )

Units Sold = SUM ( sales_clean[quantity] )
```

## Time intelligence

```DAX
Sales LY = CALCULATE ( [Total Sales], SAMEPERIODLASTYEAR ( 'Calendar'[Date] ) )

Sales YoY % = DIVIDE ( [Total Sales] - [Sales LY], [Sales LY] )

Sales YTD = TOTALYTD ( [Total Sales], 'Calendar'[Date] )

Sales Previous Month = CALCULATE ( [Total Sales], DATEADD ( 'Calendar'[Date], -1, MONTH ) )

Sales MoM % = DIVIDE ( [Total Sales] - [Sales Previous Month], [Sales Previous Month] )

Sales 3M Rolling Avg =
AVERAGEX (
    DATESINPERIOD ( 'Calendar'[Date], MAX ( 'Calendar'[Date] ), -3, MONTH ),
    CALCULATE ( [Total Sales] )
)
```

## Analysis measures

```DAX
Festive Season Sales =
CALCULATE ( [Total Sales], sales_clean[order_month] IN { 10, 11 } )

Festive Share % = DIVIDE ( [Festive Season Sales], [Total Sales] )

Loss Orders =
CALCULATE ( [Total Orders], sales_clean[profit] < 0 )

Sales Share % =
DIVIDE ( [Total Sales], CALCULATE ( [Total Sales], ALLSELECTED ( sales_clean[category] ) ) )

Category Rank =
RANKX ( ALL ( sales_clean[category] ), [Total Sales], , DESC, DENSE )

Avg Shipping Days = AVERAGE ( sales_clean[shipping_days] )
```

## Calculated column: discount band

**Table view → New column:**

```DAX
Discount Band =
SWITCH (
    TRUE (),
    sales_clean[discount] = 0, "0%",
    sales_clean[discount] <= 0.10, "1-10%",
    sales_clean[discount] <= 0.20, "11-20%",
    "21%+"
)
```

## Formatting tips

- `Total Sales`, `Total Profit`, `Avg Order Value`: Currency, ₹ symbol, 0 decimals
- All `%` measures: Percentage, 1 decimal
- Power BI has no built-in lakh/crore display unit. Use Thousands/Millions, or create `Sales (Lakh) = DIVIDE ( [Total Sales], 100000 )` for card visuals.

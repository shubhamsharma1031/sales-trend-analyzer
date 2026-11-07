-- ============================================================
-- Sales Trend Analyzer: business analysis queries (MySQL 8.0+)
-- Each query answers one business question.
-- ============================================================
USE sales_analytics;

-- ------------------------------------------------------------
-- Q1. What are the headline KPIs?
-- ------------------------------------------------------------
SELECT
    ROUND(SUM(sales), 2)                              AS total_sales,
    ROUND(SUM(profit), 2)                             AS total_profit,
    ROUND(SUM(profit) / SUM(sales) * 100, 2)          AS profit_margin_pct,
    COUNT(DISTINCT order_id)                          AS total_orders,
    COUNT(DISTINCT customer_id)                       AS total_customers,
    ROUND(SUM(sales) / COUNT(DISTINCT order_id), 2)   AS avg_order_value
FROM sales_orders;

-- ------------------------------------------------------------
-- Q2. How did sales and profit change year over year?
-- ------------------------------------------------------------
WITH yearly AS (
    SELECT order_year, SUM(sales) AS sales, SUM(profit) AS profit
    FROM sales_orders
    GROUP BY order_year
)
SELECT
    order_year,
    ROUND(sales, 2)  AS sales,
    ROUND(profit, 2) AS profit,
    ROUND((sales - LAG(sales) OVER (ORDER BY order_year))
          / LAG(sales) OVER (ORDER BY order_year) * 100, 2) AS sales_growth_pct
FROM yearly
ORDER BY order_year;

-- ------------------------------------------------------------
-- Q3. Monthly trend with month-over-month growth and running total
-- ------------------------------------------------------------
WITH monthly AS (
    SELECT order_period, SUM(sales) AS sales
    FROM sales_orders
    GROUP BY order_period
)
SELECT
    order_period,
    ROUND(sales, 2) AS sales,
    ROUND((sales - LAG(sales) OVER (ORDER BY order_period))
          / LAG(sales) OVER (ORDER BY order_period) * 100, 2)  AS mom_growth_pct,
    ROUND(SUM(sales) OVER (ORDER BY order_period), 2)            AS running_total
FROM monthly
ORDER BY order_period;

-- ------------------------------------------------------------
-- Q4. Which category and sub-category earn the most, and at what margin?
-- ------------------------------------------------------------
SELECT
    category,
    sub_category,
    ROUND(SUM(sales), 2)                      AS sales,
    ROUND(SUM(profit), 2)                     AS profit,
    ROUND(SUM(profit) / SUM(sales) * 100, 2)  AS margin_pct
FROM sales_orders
GROUP BY category, sub_category
ORDER BY category, profit DESC;

-- ------------------------------------------------------------
-- Q5. Share of total sales by category
-- ------------------------------------------------------------
SELECT
    category,
    ROUND(SUM(sales), 2) AS sales,
    ROUND(SUM(sales) / SUM(SUM(sales)) OVER () * 100, 2) AS sales_share_pct
FROM sales_orders
GROUP BY category
ORDER BY sales DESC;

-- ------------------------------------------------------------
-- Q6. Top 10 products by profit
-- ------------------------------------------------------------
SELECT
    product_name,
    category,
    SUM(quantity)            AS units_sold,
    ROUND(SUM(sales), 2)     AS sales,
    ROUND(SUM(profit), 2)    AS profit
FROM sales_orders
GROUP BY product_name, category
ORDER BY profit DESC
LIMIT 10;

-- ------------------------------------------------------------
-- Q7. Best-performing state within each region (window ranking)
-- ------------------------------------------------------------
WITH state_sales AS (
    SELECT region, state, SUM(sales) AS sales
    FROM sales_orders
    GROUP BY region, state
),
ranked AS (
    SELECT region, state, sales,
           RANK() OVER (PARTITION BY region ORDER BY sales DESC) AS rank_in_region
    FROM state_sales
)
SELECT region, state, ROUND(sales, 2) AS sales
FROM ranked
WHERE rank_in_region = 1
ORDER BY sales DESC;

-- ------------------------------------------------------------
-- Q8. How do discounts affect profit margin?
-- ------------------------------------------------------------
SELECT
    CASE
        WHEN discount = 0     THEN '0% (no discount)'
        WHEN discount <= 0.10 THEN '1-10%'
        WHEN discount <= 0.20 THEN '11-20%'
        ELSE '21%+'
    END                                         AS discount_band,
    COUNT(*)                                    AS orders,
    ROUND(SUM(sales), 2)                        AS sales,
    ROUND(SUM(profit), 2)                       AS profit,
    ROUND(SUM(profit) / SUM(sales) * 100, 2)    AS margin_pct
FROM sales_orders
GROUP BY discount_band
ORDER BY MIN(discount);

-- ------------------------------------------------------------
-- Q9. How much of the year's sales come from the festive season (Oct-Nov)?
-- ------------------------------------------------------------
SELECT
    order_year,
    ROUND(SUM(CASE WHEN order_month IN (10, 11) THEN sales ELSE 0 END), 2)        AS festive_sales,
    ROUND(SUM(sales), 2)                                                         AS total_sales,
    ROUND(SUM(CASE WHEN order_month IN (10, 11) THEN sales ELSE 0 END)
          / SUM(sales) * 100, 2)                                                 AS festive_share_pct
FROM sales_orders
GROUP BY order_year
ORDER BY order_year;

-- ------------------------------------------------------------
-- Q10. Which customer segment is most valuable?
-- ------------------------------------------------------------
SELECT
    segment,
    COUNT(DISTINCT customer_id)                         AS customers,
    ROUND(SUM(sales), 2)                                AS sales,
    ROUND(SUM(sales) / COUNT(DISTINCT customer_id), 2)  AS sales_per_customer,
    ROUND(SUM(profit) / SUM(sales) * 100, 2)            AS margin_pct
FROM sales_orders
GROUP BY segment
ORDER BY sales DESC;

-- ------------------------------------------------------------
-- Q11. Top 10 customers by lifetime value, with order count
-- ------------------------------------------------------------
SELECT
    customer_id,
    COUNT(*)                 AS orders,
    ROUND(SUM(sales), 2)     AS lifetime_sales,
    MIN(order_date)          AS first_order,
    MAX(order_date)          AS last_order
FROM sales_orders
GROUP BY customer_id
ORDER BY lifetime_sales DESC
LIMIT 10;

-- ------------------------------------------------------------
-- Q12. Pareto check: what share of sales comes from the top 20% of customers?
-- ------------------------------------------------------------
WITH customer_sales AS (
    SELECT customer_id, SUM(sales) AS sales
    FROM sales_orders
    GROUP BY customer_id
),
bucketed AS (
    SELECT customer_id, sales,
           NTILE(5) OVER (ORDER BY sales DESC) AS quintile
    FROM customer_sales
)
SELECT
    ROUND(SUM(CASE WHEN quintile = 1 THEN sales ELSE 0 END) / SUM(sales) * 100, 2)
        AS top_20pct_customers_sales_share
FROM bucketed;

-- ------------------------------------------------------------
-- Q13. Shipping performance by ship mode
-- ------------------------------------------------------------
SELECT
    ship_mode,
    COUNT(*)                        AS orders,
    ROUND(AVG(shipping_days), 2)    AS avg_shipping_days,
    MAX(shipping_days)              AS max_shipping_days
FROM sales_orders
GROUP BY ship_mode
ORDER BY avg_shipping_days;

-- ------------------------------------------------------------
-- Q14. Loss-making orders: where are we losing money?
-- ------------------------------------------------------------
SELECT
    category,
    sub_category,
    COUNT(*)                 AS loss_orders,
    ROUND(SUM(profit), 2)    AS total_loss,
    ROUND(AVG(discount) * 100, 1) AS avg_discount_pct
FROM sales_orders
WHERE profit < 0
GROUP BY category, sub_category
ORDER BY total_loss
LIMIT 10;

-- ------------------------------------------------------------
-- Q15. Best month of each year (window function + filter)
-- ------------------------------------------------------------
WITH monthly AS (
    SELECT order_year, order_month, month_name, SUM(sales) AS sales
    FROM sales_orders
    GROUP BY order_year, order_month, month_name
)
SELECT order_year, month_name, ROUND(sales, 2) AS sales
FROM (
    SELECT monthly.*,
           ROW_NUMBER() OVER (PARTITION BY order_year ORDER BY sales DESC) AS rn
    FROM monthly
) t
WHERE rn = 1
ORDER BY order_year;

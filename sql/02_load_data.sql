-- ============================================================
-- Load the cleaned CSV into MySQL
-- Run clean_data.py first so data/clean/sales_clean.csv exists.
--
-- If you get "Loading local data is disabled", run once as root:
--     SET GLOBAL local_infile = 1;
-- and connect with:  mysql --local-infile=1 -u root -p
-- (MySQL Workbench users can instead use: right-click table > Table Data Import Wizard)
-- ============================================================
USE sales_analytics;

LOAD DATA LOCAL INFILE 'data/clean/sales_clean.csv'
INTO TABLE sales_orders
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(order_id, order_date, ship_date, ship_mode, customer_id, segment, region, state, city,
 category, sub_category, product_name, quantity, unit_price, discount, sales, cost, profit,
 shipping_days, profit_margin, order_year, order_month, month_name, order_period);

-- Quick checks
SELECT COUNT(*) AS total_rows FROM sales_orders;                 -- expected: 5000
SELECT MIN(order_date), MAX(order_date) FROM sales_orders;        -- expected: 2023-01-01 to 2024-12-31

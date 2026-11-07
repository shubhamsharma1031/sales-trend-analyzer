-- ============================================================
-- Sales Trend Analyzer: database setup (MySQL 8.0+)
-- ============================================================
CREATE DATABASE IF NOT EXISTS sales_analytics;
USE sales_analytics;

DROP TABLE IF EXISTS sales_orders;

CREATE TABLE sales_orders (
    order_id       VARCHAR(20)   PRIMARY KEY,
    order_date     DATE          NOT NULL,
    ship_date      DATE          NOT NULL,
    ship_mode      VARCHAR(20)   NOT NULL,
    customer_id    VARCHAR(12)   NOT NULL,
    segment        VARCHAR(20)   NOT NULL,
    region         VARCHAR(10)   NOT NULL,
    state          VARCHAR(40)   NOT NULL,
    city           VARCHAR(40)   NOT NULL,
    category       VARCHAR(30)   NOT NULL,
    sub_category   VARCHAR(30)   NOT NULL,
    product_name   VARCHAR(80)   NOT NULL,
    quantity       INT           NOT NULL,
    unit_price     DECIMAL(10,2) NOT NULL,
    discount       DECIMAL(4,2)  NOT NULL,
    sales          DECIMAL(12,2) NOT NULL,
    cost           DECIMAL(12,2) NOT NULL,
    profit         DECIMAL(12,2) NOT NULL,
    shipping_days  INT           NOT NULL,
    profit_margin  DECIMAL(6,4)  NOT NULL,
    order_year     INT           NOT NULL,
    order_month    INT           NOT NULL,
    month_name     CHAR(3)       NOT NULL,
    order_period   CHAR(7)       NOT NULL
);

-- Indexes on columns used for filtering and grouping
CREATE INDEX idx_sales_order_date ON sales_orders (order_date);
CREATE INDEX idx_sales_category   ON sales_orders (category, sub_category);
CREATE INDEX idx_sales_region     ON sales_orders (region, state);

-- 1. Total companies
SELECT COUNT(*) FROM companies;

-- 2. List all companies
SELECT * FROM companies;

-- 3. Profit and Loss data
SELECT * FROM profitandloss;

-- 4. Balance Sheet data
SELECT * FROM balancesheet;

-- 5. Cash Flow data
SELECT * FROM cashflow;

-- 6. Stock Prices
SELECT * FROM stock_prices;

-- 7. Financial Ratios
SELECT * FROM financial_ratios;

-- 8. Sector-wise companies
SELECT sector, COUNT(*) AS total_companies
FROM companies
GROUP BY sector;

-- 9. Average Profit
SELECT AVG(profit) AS average_profit
FROM profitandloss;

-- 10. Top 10 companies by sales
SELECT company_id, sales
FROM profitandloss
ORDER BY sales DESC
LIMIT 10;
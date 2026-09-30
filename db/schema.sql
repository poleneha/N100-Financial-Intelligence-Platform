CREATE TABLE companies (
    company_id INTEGER PRIMARY KEY,
    company_name TEXT,
    ticker TEXT,
    sector TEXT
);

CREATE TABLE profitandloss (
    id INTEGER PRIMARY KEY,
    company_id INTEGER,
    year INTEGER,
    sales REAL,
    profit REAL,
    FOREIGN KEY(company_id) REFERENCES companies(company_id)
);

CREATE TABLE balancesheet (
    id INTEGER PRIMARY KEY,
    company_id INTEGER,
    year INTEGER,
    assets REAL,
    liabilities REAL,
    FOREIGN KEY(company_id) REFERENCES companies(company_id)
);

CREATE TABLE cashflow (
    id INTEGER PRIMARY KEY,
    company_id INTEGER,
    year INTEGER,
    operating_cashflow REAL,
    investing_cashflow REAL,
    financing_cashflow REAL,
    FOREIGN KEY(company_id) REFERENCES companies(company_id)
);

CREATE TABLE analysis (
    id INTEGER PRIMARY KEY,
    company_id INTEGER,
    analysis TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(company_id)
);

CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    company_id INTEGER,
    document_name TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(company_id)
);

CREATE TABLE prosandcons (
    id INTEGER PRIMARY KEY,
    company_id INTEGER,
    pros TEXT,
    cons TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(company_id)
);

CREATE TABLE sectors (
    sector_id INTEGER PRIMARY KEY,
    sector_name TEXT
);

CREATE TABLE stock_prices (
    id INTEGER PRIMARY KEY,
    company_id INTEGER,
    date TEXT,
    close_price REAL,
    FOREIGN KEY(company_id) REFERENCES companies(company_id)
);

CREATE TABLE financial_ratios (
    id INTEGER PRIMARY KEY,
    company_id INTEGER,
    year INTEGER,

    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,
    return_on_assets_pct REAL,
    debt_to_equity REAL,
    interest_coverage REAL,
    asset_turnover REAL,

    revenue_cagr_5yr REAL,
    pat_cagr_5yr REAL,
    eps_cagr_5yr REAL,

    free_cash_flow REAL,
    capex_intensity REAL,
    fcf_conversion REAL,

    composite_quality_score REAL,

    FOREIGN KEY(company_id) REFERENCES companies(company_id)
);

CREATE TABLE peer_groups (
    id INTEGER PRIMARY KEY,
    company_id INTEGER,
    peer_company TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(company_id)
);
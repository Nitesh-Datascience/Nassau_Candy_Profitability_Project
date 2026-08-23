# Nassau Candy Distributor - Product Line Profitability & Margin Performance Analysis

An end-to-end analytics project built from the supplied **Nassau Candy Distributor.csv** dataset.

## Project objective
Identify which products and divisions truly drive gross profit, detect margin risk, quantify profit concentration, diagnose cost-heavy SKUs, and operationalize the analysis in a Streamlit dashboard.

## Key validated findings
- Total sales: **$141,783.63**
- Gross profit: **$93,442.80**
- Overall gross margin: **65.91%**
- Chocolate: **92.88% of revenue** and **95.06% of gross profit**
- 5 of 15 products are sufficient to exceed **80% of both revenue and profit**
- Highest gross-profit product: **Wonka Bar - Scrumdiddlyumptious** (~$19,357.50; 69.44% margin)
- Primary margin-risk SKU: **Kazookles** (~7.69% margin; ~$0.25 profit/unit)
- No dominant high-sales/low-margin product was found among the five core chocolate products
- Margin volatility is effectively zero in this dataset because product economics are nearly fixed over time

## Data-quality note
Order dates span 2024-01-02 to 2025-12-31, while ship dates span 2026-06-30 to 2030-06-28. Therefore the project does **not** make shipping-delay, delivery-time, route-efficiency, or congestion conclusions from these fields.

## Project structure
```text
Nassau_Candy_Profitability_Project/
├── app.py                         # Streamlit dashboard
├── analysis.py                    # Cleaning + KPI + aggregation pipeline
├── make_charts.py                 # Static report chart generation
├── requirements.txt
├── README.md
├── Nassau_Candy_Profitability_Analysis.ipynb
├── data/
│   ├── raw_nassau_candy.csv
│   └── cleaned_nassau_candy.csv
├── outputs/
│   ├── product_profitability.csv
│   ├── division_performance.csv
│   ├── pareto_revenue.csv
│   └── pareto_profit.csv
├── assets/                        # Report visuals
└── report/
    ├── Nassau_Candy_Profitability_Research_Report.docx
    ├── Nassau_Candy_Profitability_Research_Report.pdf
    ├── Nassau_Candy_Executive_Stakeholder_Summary.docx
    └── Nassau_Candy_Executive_Stakeholder_Summary.pdf
```

## Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python analysis.py
streamlit run app.py
```

## Dashboard modules
1. **Product Profitability Overview** - gross-profit leaderboard, margin leaderboard, margin-risk flags.
2. **Division Performance** - revenue vs profit, division margin and share comparison.
3. **Cost & Margin Diagnostics** - cost-sales scatter, sales-margin scatter, SKU action recommendations.
4. **Profit Concentration** - revenue/profit Pareto charts and 80% dependency indicator.
5. **Data Explorer** - filtered transaction data and CSV export.

## User controls
- Order-date range
- Division filter
- Margin threshold slider
- Product search

## Action rules used in the dashboard
- **Critical:** margin < 20% → urgent reprice/cost/discontinuation review
- **High:** margin 20%-50% → reprice or renegotiate cost
- **Watch:** margin 50%-60% → monitor and test pricing
- **Healthy:** margin > 60% → maintain/scale selectively

## Recommended next data
For a production-grade contribution-margin model, add freight, warehouse/handling cost, promotions/discounts, returns, rebates, supplier cost history, and customer cost-to-serve.

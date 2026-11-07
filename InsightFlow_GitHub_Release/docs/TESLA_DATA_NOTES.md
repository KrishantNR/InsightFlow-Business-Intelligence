# Tesla 2021–2025 demo dataset notes

## Scope

The file `data/Tesla_2021_2025_Company_Data.csv` is a compact annual extract with **5 rows and 52 columns**, covering fiscal years 2021–2025. Financial statement fields are generally in USD millions. Vehicle and infrastructure measures are counts; storage deployments are in GWh; percentage fields are calculated ratios.

This is not every disclosure in Tesla's annual reports. It is not a monthly, customer-level, product-price, share-price or transaction dataset. It contains no employee headcount or employee-location breakdown. InsightFlow must not invent those dimensions.

## Missing values

The CSV has five missing cells:

- `inventory_usd_m` for 2021.
- `revenue_us_usd_m`, `revenue_china_usd_m` and `revenue_other_geographies_usd_m` for 2025.
- `revenue_yoy_pct` for 2021, because a prior-year base is not present in this five-year extract.

Blank values mean not included or not verified in this compact extract; they are not zero.

## Selected observations

- Revenue rose from USD 53,823 million in 2021 to USD 94,827 million in 2025, an increase of approximately 76.2% across the endpoints. Revenue peaked in the selected period at USD 97,690 million in 2024, then declined approximately 2.9% in 2025.
- Vehicle deliveries rose from 936,222 in 2021 to 1,636,129 in 2025; the 2025 level was below the 2023 and 2024 values.
- Storage deployments increased from 4.0 GWh in 2021 to 46.7 GWh in 2025.
- Energy generation and storage revenue increased from USD 2,789 million in 2021 to USD 12,771 million in 2025.
- Gross profit was USD 20,853 million in 2022 and USD 17,094 million in 2025.
- Operating income was USD 13,656 million in 2022 and USD 4,355 million in 2025.
- 2023 net income included a substantial deferred-tax valuation allowance release discussed in Tesla's 2024 annual report. Interpret 2023 net margin cautiously; it is not a clean recurring-operating-performance signal.
- 2025 operating cash flow was USD 14,747 million and capital expenditure was USD 8,527 million; the dataset's calculated operating cash flow less capex is USD 6,220 million.

These are descriptive observations from the bundled extract. They are not investment advice or an external rating of Tesla's business.

## Forecast caution

The dataset has only five annual observations. The 2026 linear regression output is an educational demonstration of model fitting and extrapolation; it is not statistically robust and is not Tesla guidance. The application does not model business cycles, macroeconomic conditions, pricing, competition, product mix or other causal drivers.

## Primary sources used for the compact extract

- [Tesla 2025 Form 10-K — SEC](https://www.sec.gov/Archives/edgar/data/1318605/000162828026003952/tsla-20251231.htm)
- [Tesla 2024 Form 10-K — SEC](https://www.sec.gov/Archives/edgar/data/1318605/000162828025003063/tsla-20241231.htm)
- [Tesla 2023 Form 10-K — SEC](https://www.sec.gov/Archives/edgar/data/1318605/000162828024002390/tsla-20231231.htm)
- [Tesla 2022 Form 10-K — SEC](https://www.sec.gov/Archives/edgar/data/1318605/000095017023001409/tsla-20221231.htm)
- [Tesla Q4 2024 investor update](https://digitalassets.tesla.com/tesla-contents/image/upload/IR/TSLA-Q4-2024-Update.pdf)
- [Tesla Q4 2025 production, deliveries and deployments](https://ir.tesla.com/press-release/tesla-fourth-quarter-2025-production-deliveries-deployments)

`docs/TESLA_DATA_SOURCE_REPORT.txt` contains the accompanying source/method notes originally prepared with the dataset.

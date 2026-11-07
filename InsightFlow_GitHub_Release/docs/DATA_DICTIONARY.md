# Tesla demo data dictionary

Source file: `data/Tesla_2021_2025_Company_Data.csv`  
Shape: 5 annual records × 52 fields  
Reporting period: fiscal years ended December 31, 2021–2025  
Currency: USD; financial values in USD millions unless the field name says otherwise.

| Field | Meaning | Unit / notes |
|---|---|---|
| `fiscal_year` | Fiscal year ending December 31 | Year |
| `company` | Reporting company name | Text |
| `ticker` | Trading ticker in the source extract | Text |
| `currency` | Currency for financial statement fields | ISO-like currency label; USD in this extract |
| `revenue_total_usd_m` | Total consolidated revenue | USD millions |
| `automotive_revenue_usd_m` | Automotive segment revenue | USD millions |
| `automotive_sales_usd_m` | Automotive sales revenue | USD millions |
| `automotive_regulatory_credits_usd_m` | Automotive regulatory credit revenue | USD millions |
| `automotive_leasing_usd_m` | Automotive leasing revenue | USD millions |
| `energy_generation_storage_revenue_usd_m` | Energy generation and storage revenue | USD millions |
| `services_other_revenue_usd_m` | Services and other revenue | USD millions |
| `cost_of_revenue_usd_m` | Cost of revenue | USD millions |
| `gross_profit_usd_m` | Gross profit | USD millions |
| `operating_expenses_usd_m` | Total operating expenses | USD millions |
| `research_development_usd_m` | Research and development expense | USD millions |
| `selling_general_admin_usd_m` | Selling, general and administrative expense | USD millions |
| `operating_income_usd_m` | Operating income | USD millions |
| `net_income_usd_m` | Net income | USD millions |
| `net_income_attributable_common_usd_m` | Net income attributable to common stockholders | USD millions |
| `diluted_eps_usd` | Diluted earnings per share | USD/share |
| `operating_cash_flow_usd_m` | Net cash provided by operating activities | USD millions |
| `capital_expenditures_usd_m` | Capital expenditures | USD millions |
| `cash_and_equivalents_usd_m` | Cash and cash equivalents | USD millions |
| `short_term_investments_usd_m` | Short-term investments | USD millions |
| `inventory_usd_m` | Inventory | USD millions; 2021 is blank in this extract |
| `total_assets_usd_m` | Total assets | USD millions |
| `total_liabilities_usd_m` | Total liabilities | USD millions |
| `stockholders_equity_usd_m` | Stockholders' equity | USD millions |
| `vehicle_production_units` | Total vehicle production | Vehicles |
| `vehicle_deliveries_units` | Total vehicle deliveries | Vehicles |
| `storage_deployed_gwh` | Energy storage deployed | GWh |
| `model_3_y_production_units` | Model 3/Y production | Vehicles |
| `other_models_production_units` | Other-model production | Vehicles |
| `model_3_y_deliveries_units` | Model 3/Y deliveries | Vehicles |
| `other_models_deliveries_units` | Other-model deliveries | Vehicles |
| `tesla_locations` | Tesla locations included in the annual operating extract | Count; scope may differ from a full location inventory |
| `supercharger_stations` | Supercharger stations | Count |
| `supercharger_connectors` | Supercharger connectors | Count |
| `revenue_us_usd_m` | Revenue attributed to the US | USD millions; not supplied for 2025 |
| `revenue_china_usd_m` | Revenue attributed to China | USD millions; not supplied for 2025 |
| `revenue_other_geographies_usd_m` | Revenue attributed to other geographies | USD millions; not supplied for 2025 |
| `data_notes` | Source/coverage note for the row | Text |
| `revenue_yoy_pct` | Year-over-year total revenue growth | Percent; 2021 blank because no prior-year row is included |
| `gross_margin_pct` | Gross profit divided by total revenue | Percent; calculated |
| `operating_margin_pct` | Operating income divided by total revenue | Percent; calculated |
| `net_margin_pct` | Net income divided by total revenue | Percent; calculated; 2023 has a tax-related comparability caveat |
| `delivery_to_production_ratio_pct` | Deliveries divided by production | Percent; calculated |
| `operating_cash_flow_less_capex_usd_m` | Operating cash flow less capital expenditures | USD millions; calculated |
| `cash_and_short_term_investments_usd_m` | Cash and cash equivalents plus short-term investments | USD millions; calculated |
| `automotive_revenue_share_pct` | Automotive revenue divided by total revenue | Percent; calculated |
| `energy_revenue_share_pct` | Energy generation and storage revenue divided by total revenue | Percent; calculated |
| `services_revenue_share_pct` | Services and other revenue divided by total revenue | Percent; calculated |

## General unit interpretation

- Suffix `_usd_m`: USD millions. Divide by 1,000 to express as USD billions.
- Suffix `_units`: physical unit counts.
- Suffix `_gwh`: gigawatt-hours.
- Suffix `_pct`: percentages, typically derived from other reported fields.
- Blank cells are missing/not supplied/not verified in this extract, never a numeric zero.

This is a compact teaching dataset, not a complete reproduction of every Tesla SEC disclosure.

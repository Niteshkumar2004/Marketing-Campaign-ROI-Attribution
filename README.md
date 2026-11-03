# Marketing Campaign ROI & Attribution Modeling

An interactive marketing analytics dashboard built with **Python, Pandas, Streamlit, and Plotly**. It helps marketing teams compare channel efficiency, understand how attribution rules change revenue credit, and explore a simple budget reallocation scenario.

![Dashboard](docs/dashboard-preview.png)

## Business problem
Marketing teams invest across Social Media, Email, and Paid Search, but need a consistent view of which campaigns deliver efficient acquisition and revenue. This project brings campaign performance and customer journey touchpoints into one dashboard.

## Key features
- Clean, filter, and analyze campaign spend, impressions, clicks, conversions, and revenue.
- Compare **First-Touch**, **Last-Touch**, and **Multi-Touch** attribution.
- Calculate channel and campaign **ROI**, **ROAS**, and **CPA**.
- Interactive date and channel filters.
- Budget reallocation scenario based on observed channel ROI.
- Reproducible synthetic datasets included in `data/`.

## Dashboard preview
Run the app locally to explore the interactive charts and tables.

## Attribution methodology
- **First-Touch:** 100% of a converting customer's revenue is credited to the first channel in the recorded journey.
- **Last-Touch:** 100% is credited to the final channel.
- **Multi-Touch:** revenue is distributed across touchpoints using increasing linear weights by touchpoint position (1, 2, 3, ...). The weights are normalized to sum to 100%.

These are rule-based attribution models. They are useful for comparing perspectives, but they do not establish causal incrementality.

## KPI definitions
| KPI | Formula |
|---|---|
| ROI | `(Revenue - Ad Spend) / Ad Spend × 100` |
| ROAS | `Revenue / Ad Spend` |
| CPA | `Ad Spend / Conversions` |
| Conversion rate | `Conversions / Clicks` (can be added from source data) |

## Project structure
```text
marketing-campaign-roi-attribution/
├── app.py
├── data/
│   ├── campaign_performance.csv
│   └── customer_journeys.csv
├── docs/
│   └── dashboard-preview.png
├── requirements.txt
├── .gitignore
└── README.md
```

## Run locally
1. Install Python 3.10 or newer.
2. Clone this repository:
   ```bash
   git clone https://github.com/YOUR-USERNAME/marketing-campaign-roi-attribution.git
   cd marketing-campaign-roi-attribution
   ```
3. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv .venv
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   # macOS / Linux
   source .venv/bin/activate
   ```
4. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
5. Launch the dashboard:
   ```bash
   streamlit run app.py
   ```

## Data dictionary

### `campaign_performance.csv`
| Column | Description |
|---|---|
| date | Campaign reporting date |
| channel | Social Media, Email, or Paid Search |
| campaign | Campaign name |
| ad_spend | Daily advertising spend in USD |
| impressions | Number of ad impressions |
| clicks | Number of clicks |
| conversions | Number of conversions |
| revenue | Revenue associated with conversions, USD |

### `customer_journeys.csv`
| Column | Description |
|---|---|
| customer_id | Anonymous synthetic customer key |
| touchpoint_order | Position of touchpoint in journey |
| touchpoint_date | Touchpoint date |
| channel | Marketing channel for touchpoint |
| campaign | Campaign name |
| converted | 1 if journey converted, otherwise 0 |
| conversion_value | Order value stored on final touchpoint only |

## Replace demo data with real data
Keep the column names and data types consistent with the data dictionary. Before combining platform exports:
- Standardize channel and campaign naming.
- Normalize dates and currency.
- Deduplicate conversion IDs.
- Use a shared anonymous customer or session key for journey stitching.
- Define a consistent conversion window and timezone.
- Exclude internal/test traffic and invalid spend rows.

## Limitations and next steps
- Included data is synthetic and intended for portfolio demonstration, not business decisions.
- The multi-touch model is position-weighted linear credit, not a data-driven or causal model.
- A production implementation should add currency configuration, conversion-window logic, confidence intervals, incremental lift tests, and connectors to ad platforms/analytics tools.
- The current budget suggestion is a transparent scenario, not an automatic optimizer.

## Suggested GitHub topics
`marketing-analytics` `attribution-modeling` `roi-analysis` `python` `streamlit` `plotly` `data-analytics`

## License
MIT. Add a `LICENSE` file if you intend to distribute this project under the MIT License.

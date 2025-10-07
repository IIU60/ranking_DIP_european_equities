# Equities Ranking Platform

**Live Streamlit App:** [Add deployment link here]( )

## Overview
This repository houses the quantitative equity ranking workstation developed by the Quantitative Department at A&G Banca Privada. The platform combines a Streamlit dashboard with reproducible data-retrieval utilities that source factor indicators from Refinitiv Eikon. Analysts can explore cross-sectional factor behaviour, craft composite scores, and monitor out-of-sample performance across European equity universes.

![Dashboard preview](path-to-dashboard-image.png)
> _Replace `path-to-dashboard-image.png` with the actual image file you would like to showcase._

## Explore the dashboard
The Streamlit app (located in [`app/`](app/)) is the heart of the project. Key areas of the interface include:

- **Data onboarding panel** – Define the working universe, pick the indicator directory, and set data-quality thresholds before the workspace loads.
- **Ranking workspace** – Review raw indicator distributions, create quantile-based factor ranks, and blend indicators using arithmetic or weighted formulas.
- **Score comparison & exports** – Visualise relative performance through tables and charts, then export selected scores or price histories to CSV for further research.
- **Diagnostic widgets** – Surface missing data warnings, factor metadata, and configuration summaries so users can iterate quickly.

Once launched, the application reads the precomputed datasets, calculates rankings in real time, and updates visualisations interactively as users adjust parameters.

### How the layout fits together
1. **Sidebar configuration** – Users select universes, factor groups, and data lags while validating data coverage.
2. **Ranking view** – Central tables and charts reveal individual factor behaviour and aggregated composite scores.
3. **Detail drill-downs** – Modal views display historical trends, percentile shifts, and metadata for each indicator.
4. **Export actions** – Contextual buttons allow analysts to download CSVs or push summary tables for reporting pipelines.

These building blocks are described in greater detail (with screenshots) in the internal documentation inside [`Docs/docs_plataforma.md`](Docs/docs_plataforma.md).

## Data pipeline components
To power the dashboard, the repository includes reproducible scripts and notebooks under [`eikon_data_retrieval/`](eikon_data_retrieval/) that automate:

- Indicator downloads via the utilities in [`data_retrieval.py`](eikon_data_retrieval/data_retrieval.py), which handle pagination and rate limits when pulling from Eikon.
- Index mask creation so the universe used in the dashboard matches benchmark constituents over time.
- Daily refresh workflows through the notebooks [`mass_download_notebook.ipynb`](eikon_data_retrieval/mass_download_notebook.ipynb) and [`download_calcs_ranking.ipynb`](eikon_data_retrieval/download_calcs_ranking.ipynb), mirroring the production schedule outlined in [`Docs/docs_descarga_de_datos.md`](Docs/docs_descarga_de_datos.md).

Spanish-language guides in the [`Docs/`](Docs/) folder walk through installation, data extraction, and dashboard operation in depth, complete with screenshots and troubleshooting tips.

## Getting started
### Prerequisites
- Python 3.10.9
- Access to the Refinitiv Eikon desktop client and an API App Key
- Conda (recommended) or an alternative virtual environment manager

### Installation
1. Clone the repository to your local machine using GitHub Desktop or your preferred Git client.
2. Create and activate a virtual environment (e.g. `conda create -n equities_ranking python=3.10.9` followed by `conda activate equities_ranking`).
3. Install application dependencies:
   - `pip install -r app/app_requirements.txt` for the Streamlit interface
   - `pip install -r eikon_data_retrieval/data_requirements.txt` for the Eikon download scripts
4. (Optional) Duplicate the `nominal_*_requirements.txt` files if you need a lighter dependency set for experimentation.

### Configure Eikon access
1. Install the Refinitiv Eikon desktop application and log in with your credentials.
2. Generate an App Key via the Eikon “App Key Generator” (select “Eikon Data API”).
3. Create a `.env` file in the repository root containing `EIKON_APP_KEY=<your key>` so the download notebooks can authenticate with the API.

### Run the dashboard locally
1. Launch the configured virtual environment.
2. Navigate to the [`app/`](app/) directory and start the dashboard:
   ```bash
   streamlit run app.py
   ```
3. Use the sidebar to point the app to your data directory and tweak indicator filters. The workspace will then populate ranking tables, performance plots, and export options in line with your selections.

## Contributing
Issues and enhancements can be tracked through the repository issue list. For substantial changes, please open a discussion outlining the proposed workflow or interface updates before submitting a pull request.

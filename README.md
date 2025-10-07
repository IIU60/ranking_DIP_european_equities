# Equities Ranking Platform

**Live Streamlit App:** []()

## Overview
This repository houses the quantitative equity ranking workstation developed by the Quantitative Department at A&G Banca Privada. It combines a Streamlit dashboard with reproducible data-retrieval utilities that source factor indicators from Refinitiv Eikon. The goal is to help analysts explore cross-sectional factor behaviour, craft composite scores, and monitor out-of-sample performance across European equity universes.

> **Dashboard preview:** _Add the Streamlit screenshot here to give visitors a visual tour of the application._

## Explore the dashboard
The Streamlit app (located in `app/`) is the heart of the project. Key areas of the interface include:

- **Data onboarding panel** – Define the working universe, pick the indicator directory, and set data-quality thresholds before the workspace loads.【F:app/app.py†L22-L88】
- **Ranking workspace** – Review raw indicator distributions, create quantile-based factor ranks, and blend indicators using arithmetic or weighted formulas.【F:app/app.py†L90-L125】【F:Docs/docs_plataforma.md†L118-L178】
- **Score comparison & exports** – Visualise relative performance through tables and charts, then export selected scores or price histories to CSV for further research.【F:Docs/docs_plataforma.md†L178-L194】
- **Diagnostic widgets** – Surface missing data warnings, factor metadata, and configuration summaries so users can iterate quickly.【F:Docs/docs_plataforma.md†L100-L178】

Once launched, the application reads the precomputed datasets, calculates rankings in real time, and updates visualisations interactively as users adjust parameters.【F:app/app.py†L1-L125】

## Data pipeline components
To power the dashboard, the repository includes reproducible scripts and notebooks under `eikon_data_retrieval/` that automate:

- Indicator downloads via `download_indicators`, `vertical_download`, and `continue_download`, handling pagination and rate limits when pulling from Eikon.【F:eikon_data_retrieval/data_retrieval.py†L1-L225】
- Index mask creation so the universe used in the dashboard matches benchmark constituents over time.【F:Docs/docs_descarga_de_datos.md†L16-L208】
- Daily refresh workflows through `mass_download_notebook.ipynb` and `download_calcs_ranking.ipynb`, mirroring the production schedule outlined in the internal documentation.【F:Docs/docs_descarga_de_datos.md†L53-L208】

Spanish-language guides in the `Docs/` folder walk through installation, data extraction, and dashboard operation in depth, complete with screenshots and troubleshooting tips.【F:Docs/docs_descarga_de_datos.md†L1-L208】【F:Docs/docs_plataforma.md†L1-L194】

## Getting started
### Prerequisites
- Python 3.10.9
- Access to the Refinitiv Eikon desktop client and an API App Key
- Conda (recommended) or an alternative virtual environment manager

### Installation
1. Clone the repository to your local machine using GitHub Desktop or your preferred Git client.【F:Docs/docs_plataforma.md†L14-L53】
2. Create and activate a virtual environment (e.g. `conda create -n equities_ranking python=3.10.9` followed by `conda activate equities_ranking`).【F:Docs/docs_plataforma.md†L55-L77】
3. Install application dependencies: `pip install -r app/app_requirements.txt` for the Streamlit interface and `pip install -r eikon_data_retrieval/data_requirements.txt` for the Eikon download scripts.【F:Docs/docs_plataforma.md†L78-L98】【F:Docs/docs_descarga_de_datos.md†L53-L88】
4. (Optional) Duplicate the `nominal_*_requirements.txt` files if you need a lighter dependency set for experimentation.

### Configure Eikon access
1. Install the Refinitiv Eikon desktop application and log in with your credentials.【F:Docs/docs_descarga_de_datos.md†L89-L120】
2. Generate an App Key via the Eikon “App Key Generator” (select “Eikon Data API”).【F:Docs/docs_descarga_de_datos.md†L120-L171】
3. Create a `.env` file in the repository root containing `EIKON_APP_KEY=<your key>` so the download notebooks can authenticate with the API.【F:Docs/docs_descarga_de_datos.md†L171-L208】

### Run the dashboard locally
1. Launch the configured virtual environment.
2. Navigate to the `app/` directory and start the dashboard:
   ```bash
   streamlit run app.py
   ```
3. Use the sidebar to point the app to your data directory and tweak indicator filters. The workspace will then populate ranking tables, performance plots, and export options in line with your selections.【F:app/app.py†L11-L125】【F:Docs/docs_plataforma.md†L100-L194】

## Contributing
Issues and enhancements can be tracked through the repository issue list. For substantial changes, please open a discussion outlining the proposed workflow or interface updates before submitting a pull request.


# Autonomous Dynasty Trade Agent

A backend system designed to evaluate Dynasty Fantasy Football trades. This project demonstrates experience with ETL pipelines, relational database design, and integrating LLMs into data-driven applications.

### Overview
The Dynasty Trade Agent analyzes trades by combining historical performance data with real-time market valuations. Unlike static trade calculators, this system uses LLM-based reasoning to account for player age, production trends, and market volatility.

### Key Features
* **Trade Evaluation:** Integrates LangChain with OpenAI/Anthropic to provide context-aware trade analysis.
* **ETL Pipeline:** Custom Python scripts to ingest and normalize data from nflverse and DynastyProcess.
* **Time-Series Data:** Tracks player value fluctuations to identify strategic buy or sell opportunities.
* **Containerized Infrastructure:** PostgreSQL database managed via Docker for consistent development and deployment.

---

### Tech Stack
* **Language:** Python 3.9+
* **Database:** PostgreSQL 16
* **API Framework:** FastAPI
* **AI Framework:** LangChain / OpenAI SDK
* **Infrastructure:** Docker & Docker Compose
* **Data Sources:** nfl_data_py (nflverse), DynastyProcess (Market Values)

---

### Database Architecture
The system utilizes a normalized schema to maintain data integrity across roughly 25,000 player records and 17,000 game performance rows.

* **players:** Central registry using NFL GSIS IDs as unique identifiers to accurately distinguish players with identical names.
* **player_game_stats:** Granular box-score data including passing, rushing, and receiving metrics.
* **player_value_history:** Time-series table for tracking market value trends.
* **roster_slots:** Tracks fantasy team ownership and historical roster changes using active_from and active_to timestamps.

---

### Getting Started

#### Prerequisites
* Docker Desktop
* Python 3.9+

#### Setup
1. **Initialize the Database:**
   ```bash
   docker-compose up -d
Run Ingestion Pipelines:

Bash
python ingestion/ingest_teams.py
python ingestion/ingest_players.py
python ingestion/ingest_nfl_games.py
python ingestion/ingest_player_game_stats.py
python ingestion/ingest_player_values.py
Start the API:

Bash
uvicorn app.main:app --reload
Roadmap
[x] Database Schema Design & Normalization

[x] Dockerized PostgreSQL Environment

[x] ETL Pipelines for NFL & Market Data

[ ] FastAPI Endpoints for Player & Roster Analysis

[ ] LangChain "Advisor" implementation for Trade Reasoning

[ ] Frontend Dashboard for Trade Visualization

Resume Impact
Data Engineering: Developed idempotent ETL pipelines to synchronize multi-source data with 0% duplication using UPSERT logic.

System Design: Architected a normalized PostgreSQL database to handle large-scale sports datasets and time-series valuations.

Backend Development: Built a containerized environment using Docker to ensure environment parity and scalable API services.


Would you like me to help you draft the **FastAPI** code for the player profile endpoint next?

#schedules[['game_id', 'season', 'week', 'gameday', 'home_team', 'away_team']].head(10))

import pandas as pd
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import nfl_data_py as nfl
import psycopg2



conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="dynasty_football",
    user="dynasty_user",
    password="dynasty_pass"
)

"""
CREATE TABLE nfl_games(
    game_id SERIAL PRIMARY KEY,
    nflverse_game_id VARCHAR(50) UNIQUE,
    season INT NOT NULL,
    game_week INT NOT NULL,
    home_team_id INT NOT NULL REFERENCES nfl_team(nfl_team_id),
    away_team_id INT NOT NULL REFERENCES nfl_team(nfl_team_id),
    game_date DATE NOT NULL
);
"""

cur = conn.cursor()
games = nfl.import_schedules([2022, 2023, 2024, 2025])

for _, row in games.iterrows():
    if pd.isna(row['gameday']):
        continue
    cur.execute("""
        INSERT INTO nfl_games (nflverse_game_id, season, game_week, home_team_id, away_team_id, game_date)
        VALUES (%s, %s, %s, (SELECT nfl_team_id FROM nfl_team WHERE nfl_team_abb = %s), (SELECT nfl_team_id FROM nfl_team WHERE nfl_team_abb = %s), %s)
        ON CONFLICT (nflverse_game_id) DO UPDATE
        SET season = EXCLUDED.season,
            game_week = EXCLUDED.game_week,
            home_team_id = EXCLUDED.home_team_id,
            away_team_id = EXCLUDED.away_team_id,
            game_date = EXCLUDED.game_date
    """, (row['game_id'], row['season'], row['week'], row['home_team'], row['away_team'], row['gameday']))

conn.commit()
cur.close()
conn.close()
print("Games ingested successfully")
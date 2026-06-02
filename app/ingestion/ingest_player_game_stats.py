import pandas as pd
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import nfl_data_py as nfl
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

# Load all lookups into memory upfront
cur.execute("SELECT gsis_id, player_id FROM players WHERE gsis_id IS NOT NULL")
player_map = {row[0]: row[1] for row in cur.fetchall()}

cur.execute("SELECT nfl_team_abb, nfl_team_id FROM nfl_team")
team_map = {row[0]: row[1] for row in cur.fetchall()}

cur.execute("SELECT season, game_week, home_team_id, away_team_id, game_id FROM nfl_games")
game_map = {}
for row in cur.fetchall():
    season, week, home_id, away_id, game_id = row
    game_map[(season, week, home_id)] = game_id
    game_map[(season, week, away_id)] = game_id

weekly = nfl.import_weekly_data([2022, 2023, 2024])
skipped = 0
total = len(weekly)

for i, (_, row) in enumerate(weekly.iterrows()):
    if i % 500 == 0:
        conn.commit()
        print(f"Progress: {i}/{total} rows processed")

    if pd.isna(row['recent_team']):
        skipped += 1
        continue

    player_id = player_map.get(row['player_id'])
    team_id = team_map.get(row['recent_team'])

    if player_id is None or team_id is None:
        skipped += 1
        continue

    game_id = game_map.get((row['season'], row['week'], team_id))
    if game_id is None:
        skipped += 1
        continue

    passing_yards = 0 if pd.isna(row['passing_yards']) else int(row['passing_yards'])
    passing_tds = 0 if pd.isna(row['passing_tds']) else int(row['passing_tds'])
    interceptions = 0 if pd.isna(row['interceptions']) else int(row['interceptions'])
    receptions = 0 if pd.isna(row['receptions']) else int(row['receptions'])
    rushing_yards = 0 if pd.isna(row['rushing_yards']) else int(row['rushing_yards'])
    rushing_tds = 0 if pd.isna(row['rushing_tds']) else int(row['rushing_tds'])
    receiving_yards = 0 if pd.isna(row['receiving_yards']) else int(row['receiving_yards'])
    receiving_tds = 0 if pd.isna(row['receiving_tds']) else int(row['receiving_tds'])

    cur.execute("""
        INSERT INTO player_game_stats (player_id, nfl_team_id, game_id,
            passing_yards, passing_touchdowns, interceptions, receptions,
            rushing_yards, rushing_touchdowns, receiving_yards, receiving_touchdowns)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (player_id, game_id) DO UPDATE
        SET passing_yards = EXCLUDED.passing_yards,
            passing_touchdowns = EXCLUDED.passing_touchdowns,
            interceptions = EXCLUDED.interceptions,
            receptions = EXCLUDED.receptions,
            rushing_yards = EXCLUDED.rushing_yards,
            rushing_touchdowns = EXCLUDED.rushing_touchdowns,
            receiving_yards = EXCLUDED.receiving_yards,
            receiving_touchdowns = EXCLUDED.receiving_touchdowns
    """, (player_id, team_id, game_id, passing_yards, passing_tds, interceptions,
          receptions, rushing_yards, rushing_tds, receiving_yards, receiving_tds))

conn.commit()
cur.close()
conn.close()
print(f"Player game stats ingested successfully. Skipped {skipped} rows.")
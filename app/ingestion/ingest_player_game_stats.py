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

cur = conn.cursor()
weekly = nfl.import_weekly_data([2022, 2023, 2024])

skipped = 0

for _, row in weekly.iterrows():
    if pd.isna(row['recent_team']):
        skipped += 1
        continue

    # Look up player
    cur.execute("SELECT player_id FROM players WHERE gsis_id = %s", (row['player_id'],))
    player = cur.fetchone()
    if player is None:
        skipped += 1
        continue
    player_id = player[0]

    # Look up team
    cur.execute("SELECT nfl_team_id FROM nfl_team WHERE nfl_team_abb = %s", (row['recent_team'],))
    team = cur.fetchone()
    if team is None:
        skipped += 1
        continue
    team_id = team[0]

    # Look up game
    cur.execute("""
        SELECT game_id FROM nfl_games
        WHERE season = %s AND game_week = %s
        AND (home_team_id = %s OR away_team_id = %s)
    """, (row['season'], row['week'], team_id, team_id))
    game = cur.fetchone()
    if game is None:
        skipped += 1
        continue
    game_id = game[0]

    # Convert stats
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
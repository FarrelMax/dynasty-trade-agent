#1. Connect to the database
#2. Pull player data from nflverse
#3. Insert each player into the players table
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
CREATE TABLE players(
    player_id SERIAL PRIMARY KEY,
    player_name VARCHAR(255) NOT NULL,
    position VARCHAR(50) NOT NULL,
    nfl_team_id INT NOT NULL REFERENCES nfl_team(nfl_team_id),
    player_height INT NOT NULL,
    player_weight INT NOT NULL,
    date_of_birth DATE NOT NULL,
    draft_year INT
);
"""

cur = conn.cursor()
players = nfl.import_players()

for _, row in players.iterrows():
    if pd.isna(row['latest_team']):
        continue

    height = None if pd.isna(row['height']) else int(row['height'])
    weight = None if pd.isna(row['weight']) else int(row['weight'])
    birth_date = None if pd.isna(row['birth_date']) else row['birth_date']
    draft_year = None if pd.isna(row['draft_year']) else int(row['draft_year'])

    cur.execute("""
        INSERT INTO players (player_name, gsis_id, position, nfl_team_id, player_height, player_weight, date_of_birth, draft_year)
        VALUES (%s, %s, %s, (SELECT nfl_team_id FROM nfl_team WHERE nfl_team_abb = %s), %s, %s, %s, %s)
        ON CONFLICT (gsis_id) DO UPDATE
        SET position = EXCLUDED.position,
            nfl_team_id = EXCLUDED.nfl_team_id
    """, (row['display_name'], row['gsis_id'], row['position'], row['latest_team'], height, weight, birth_date, draft_year))

conn.commit()
cur.close()
conn.close()
print("Players ingested successfully")
    
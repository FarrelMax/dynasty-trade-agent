
import pandas as pd
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import nfl_data_py as nfl
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()  

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
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

players = players[
    (players['status'].isin(['ACT', 'RES', 'PUP', 'UFA', 'RFA'])) &
    (players['position'].isin(['QB', 'RB', 'WR', 'TE'])) &
    ((players['draft_year'] >= 2012) | (players['draft_year'].isna()))
]

team_abb_fixes = {
    'AZ': 'ARI',
    'LA': 'LAR',  
}




print(f"Filtered to {len(players)} relevant players")
total = len(players)
for i, (_, row) in enumerate(players.iterrows()):
    if pd.isna(row['latest_team']):
        continue

    height = None if pd.isna(row['height']) else int(row['height'])
    weight = None if pd.isna(row['weight']) else int(row['weight'])
    birth_date = None if pd.isna(row['birth_date']) else row['birth_date']
    draft_year = None if pd.isna(row['draft_year']) else int(row['draft_year'])

    team_abb = row['latest_team']
    team_abb = team_abb_fixes.get(team_abb, team_abb)

    cur.execute("SELECT nfl_team_id FROM nfl_team WHERE nfl_team_abb = %s", (team_abb,))
    team = cur.fetchone()
    if team is None:
        continue

    cur.execute("""
        INSERT INTO players (player_name, gsis_id, position, nfl_team_id, player_height, player_weight, date_of_birth, draft_year)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (gsis_id) DO UPDATE
        SET position = EXCLUDED.position,
            nfl_team_id = EXCLUDED.nfl_team_id
    """, (row['display_name'], row['gsis_id'], row['position'], team[0], height, weight, birth_date, draft_year))

    if i % 100 == 0:
        conn.commit() 
        print(f"Progress: {i}/{total} players processed")
conn.commit()
cur.close()
conn.close()
print("Players ingested successfully")
    
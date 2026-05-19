#1. Connect to the database
#2. Pull team data from nflverse
#3. Insert each team into the teams table
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import nfl_data_py as nfl
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()  

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

cur = conn.cursor()

teams = nfl.import_team_desc()

for _,row in teams.iterrows():
    cur.execute("""
        INSERT INTO nfl_team(nfl_team_name, nfl_team_abb)
        VALUES (%s, %s)
        ON CONFLICT (nfl_team_abb) DO UPDATE
        SET nfl_team_name = EXCLUDED.nfl_team_name
        """, (row['team_name'], row['team_abbr']))
    
conn.commit()
cur.close()
conn.close()
print("Teams ingested successfully")


import pandas as pd
import re
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
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
values = pd.read_csv('https://github.com/DynastyProcess/data/raw/master/files/values.csv')

skipped = 0
inserted = 0

for _, row in values.iterrows():
    if pd.isna(row['player']) or pd.isna(row['value_2qb']):
        skipped += 1
        continue
    clean_name = re.sub(r'\s+(Jr\.?|Sr\.?|II|III|IV|V)$', '', row['player'])

    # Look up player by name and position
    cur.execute("""
        SELECT player_id FROM players
        WHERE player_name = %s AND position = %s
        LIMIT 1
    """, (clean_name, row['pos']))

    player = cur.fetchone()
    if player is None:
        skipped += 1
        continue
    player_id = player[0]

    valuation_date = row['scrape_date']
    fantasy_value = int(row['value_2qb'])

    cur.execute("""
        INSERT INTO player_value_history (player_id, valuation_date, fantasy_value)
        VALUES (%s, %s, %s)
        ON CONFLICT DO NOTHING
    """, (player_id, valuation_date, fantasy_value))
    inserted += 1

conn.commit()
cur.close()
conn.close()
print(f"Player values ingested. Inserted: {inserted}, Skipped: {skipped}")
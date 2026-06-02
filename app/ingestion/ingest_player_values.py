import pandas as pd
import re
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

def strip_suffix(name):
    return re.sub(r'\s+(Jr\.?|Sr\.?|II|III|IV|V)$', '', name).strip()

# Load all players, strip suffixes from DB names for matching
cur.execute("SELECT player_id, player_name, position FROM players")
player_map = {}
for row in cur.fetchall():
    player_id, name, pos = row
    clean = strip_suffix(name)
    player_map[(clean, pos)] = player_id

values = pd.read_csv('https://github.com/DynastyProcess/data/raw/master/files/values.csv')

skipped = 0
inserted = 0
unmatched = []

for _, row in values.iterrows():
    if pd.isna(row['player']) or pd.isna(row['value_2qb']):
        skipped += 1
        continue

    # Skip draft picks
    if row['pos'] == 'PICK':
        skipped += 1
        continue

    clean_name = strip_suffix(row['player'])
    pos = row['pos']

    player_id = player_map.get((clean_name, pos))
    if player_id is None:
        unmatched.append((clean_name, pos))
        skipped += 1
        continue

    cur.execute("""
        INSERT INTO player_value_history (player_id, valuation_date, fantasy_value)
        VALUES (%s, %s, %s)
        ON CONFLICT DO NOTHING
    """, (player_id, row['scrape_date'], int(row['value_2qb'])))
    inserted += 1

conn.commit()
cur.close()
conn.close()
print(f"Player values ingested. Inserted: {inserted}, Skipped: {skipped}")
print(f"\nUnmatched: {len(unmatched)}")
print("First 20 unmatched:")
for name, pos in unmatched[:20]:
    print(f"  {pos}: {name}")
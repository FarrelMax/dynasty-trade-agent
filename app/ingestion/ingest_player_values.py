import pandas as pd
import ssl
import psycopg2
from datetime import datetime

# SSL Fix for macOS
ssl._create_default_https_context = ssl._create_unverified_context

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="dynasty_football",
    user="dynasty_user",
    password="dynasty_pass"
)
cur = conn.cursor()

url = 'https://github.com/DynastyProcess/data/raw/master/files/values.csv'
values_df = pd.read_csv(url)

skipped = 0
inserted = 0

# 3. Ingest Values
for _, row in values_df.iterrows():
    cur.execute("""
        SELECT player_id FROM players 
        WHERE player_name = %s AND position = %s
    """, (row['player'], row['pos']))
    
    player = cur.fetchone()
    
    if player is None:
        skipped += 1
        continue
    
    player_id = player[0]
    
    # Use value_2qb for Superflex or value_1qb based on preference. 
    # Most Dynasty enthusiasts use Superflex (2QB) values.
    trade_value = int(row['value_2qb'])
    valuation_date = row['scrape_date']

    cur.execute("""
        INSERT INTO player_value_history (player_id, valuation_date, fantasy_value)
        VALUES (%s, %s, %s)
        ON CONFLICT DO NOTHING
    """, (player_id, valuation_date, trade_value))
    
    inserted += 1

conn.commit()
cur.close()
conn.close()

print(f"Values ingested: {inserted}. Skipped (no name match): {skipped}.")
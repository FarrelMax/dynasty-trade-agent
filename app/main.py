from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import psycopg2
import psycopg2.extras

app = FastAPI(title="Dynasty Trade Agent API")

def get_db():
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="dynasty_football",
        user="dynasty_user",
        password="dynasty_pass"
    )
    return conn

# Search endpoint - must come before {player_name} routes
@app.get("/players/search/{query}")
def search_players(query: str):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT p.player_name, p.position, t.nfl_team_abb, v.fantasy_value
        FROM players p
        JOIN nfl_team t ON p.nfl_team_id = t.nfl_team_id
        LEFT JOIN player_value_history v ON p.player_id = v.player_id
        WHERE p.player_name ILIKE %s
        ORDER BY v.fantasy_value DESC NULLS LAST
        LIMIT 10
    """, (f"%{query}%",))

    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

@app.get("/players/{player_name}")
def get_player(player_name: str):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT p.player_name, p.position, t.nfl_team_abb, p.date_of_birth, p.draft_year
        FROM players p
        JOIN nfl_team t ON p.nfl_team_id = t.nfl_team_id
        WHERE p.player_name = %s
    """, (player_name,))

    player = cur.fetchone()
    if player is None:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Player not found")

    cur.close()
    conn.close()
    return player

@app.get("/players/{player_name}/value")
def get_player_value(player_name: str):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT p.player_name, p.position, t.nfl_team_abb, v.fantasy_value, v.valuation_date
        FROM players p
        JOIN nfl_team t ON p.nfl_team_id = t.nfl_team_id
        JOIN player_value_history v ON p.player_id = v.player_id
        WHERE p.player_name = %s
        ORDER BY v.valuation_date DESC
        LIMIT 1
    """, (player_name,))

    result = cur.fetchone()
    if result is None:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Player or value not found")

    cur.close()
    conn.close()
    return result

@app.get("/players/{player_name}/stats")
def get_player_stats(player_name: str, season: int = 2024):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT p.player_name, g.season, g.game_week, s.passing_yards, s.passing_touchdowns,
               s.rushing_yards, s.rushing_touchdowns, s.receptions, s.receiving_yards, s.receiving_touchdowns
        FROM player_game_stats s
        JOIN players p ON s.player_id = p.player_id
        JOIN nfl_games g ON s.game_id = g.game_id
        WHERE p.player_name = %s AND g.season = %s
        ORDER BY g.game_week
    """, (player_name, season))

    stats = cur.fetchall()
    if not stats:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="No stats found")

    cur.close()
    conn.close()
    return {"player": player_name, "season": season, "games": stats}

class TradeRequest(BaseModel):
    team_a_gives: List[str]
    team_b_gives: List[str]

@app.post("/evaluate-trade")
def evaluate_trade(trade: TradeRequest):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def get_player_values(player_names):
        players = []
        for name in player_names:
            cur.execute("""
                SELECT p.player_name, p.position, t.nfl_team_abb, v.fantasy_value
                FROM players p
                JOIN nfl_team t ON p.nfl_team_id = t.nfl_team_id
                JOIN player_value_history v ON p.player_id = v.player_id
                WHERE p.player_name = %s
                ORDER BY v.valuation_date DESC
                LIMIT 1
            """, (name,))
            result = cur.fetchone()
            if result:
                players.append(result)
            else:
                players.append({"player_name": name, "position": "Unknown", "nfl_team_abb": "N/A", "fantasy_value": 0})
        return players

    team_a_players = get_player_values(trade.team_a_gives)
    team_b_players = get_player_values(trade.team_b_gives)

    team_a_total = sum(p["fantasy_value"] for p in team_a_players)
    team_b_total = sum(p["fantasy_value"] for p in team_b_players)

    difference = team_a_total - team_b_total
    if difference > 0:
        winner = "Team A"
    elif difference < 0:
        winner = "Team B"
    else:
        winner = "Even"

    cur.close()
    conn.close()

    return {
        "team_a": {"players": team_a_players, "total_value": team_a_total},
        "team_b": {"players": team_b_players, "total_value": team_b_total},
        "difference": abs(difference),
        "winner": winner
    }
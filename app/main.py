import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import psycopg2
import psycopg2.extras
from fastapi.middleware.cors import CORSMiddleware
from app.agent.trade_agent import evaluate_trade_with_agent

load_dotenv()

app = FastAPI(title="Dynasty Trade Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    try:
        yield conn
    finally:
        conn.close()

@app.get("/players/search/{query}")
def search_players(query: str, conn=Depends(get_db)):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
    SELECT * FROM (
        SELECT DISTINCT ON (p.player_id)
            p.player_name, p.position, t.nfl_team_abb, v.fantasy_value
        FROM players p
        JOIN nfl_team t ON p.nfl_team_id = t.nfl_team_id
        LEFT JOIN player_value_history v ON p.player_id = v.player_id
        WHERE p.player_name ILIKE %s
        ORDER BY p.player_id, v.valuation_date DESC NULLS LAST
        ) sub
        ORDER BY fantasy_value DESC NULLS LAST
        LIMIT 10
    """, (f"%{query}%",))
    results = cur.fetchall()
    cur.close()
    return results


@app.get("/players/{player_name}")
def get_player(player_name: str, conn=Depends(get_db)):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT p.player_name, p.position, t.nfl_team_abb, p.date_of_birth, p.draft_year
        FROM players p
        JOIN nfl_team t ON p.nfl_team_id = t.nfl_team_id
        WHERE p.player_name ILIKE %s
        LIMIT 1
    """, (f"%{player_name}%",))
    player = cur.fetchone()
    cur.close()
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@app.get("/players/{player_name}/value-history")
def get_player_value_history(player_name: str, conn=Depends(get_db)):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT v.valuation_date, v.fantasy_value
        FROM player_value_history v
        JOIN players p ON v.player_id = p.player_id
        WHERE p.player_name ILIKE %s
        ORDER BY v.valuation_date ASC
    """, (f"%{player_name}%",))
    history = cur.fetchall()
    cur.close()
    if not history:
        raise HTTPException(status_code=404, detail="No value history found")
    return {"player": player_name, "history": history}

@app.get("/players/{player_name}/value")
def get_player_value(player_name: str, conn=Depends(get_db)):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT p.player_name, p.position, t.nfl_team_abb, v.fantasy_value, v.valuation_date
        FROM players p
        JOIN nfl_team t ON p.nfl_team_id = t.nfl_team_id
        JOIN player_value_history v ON p.player_id = v.player_id
        WHERE p.player_name ILIKE %s
        ORDER BY v.valuation_date DESC
        LIMIT 1
    """, (f"%{player_name}%",))
    result = cur.fetchone()
    cur.close()
    if result is None:
        raise HTTPException(status_code=404, detail="Player or value not found")
    return result


@app.get("/players/{player_name}/stats")
def get_player_stats(player_name: str, season: int = 2024, conn=Depends(get_db)):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT p.player_name, g.season, g.game_week,
               s.passing_yards, s.passing_touchdowns,
               s.rushing_yards, s.rushing_touchdowns,
               s.receptions, s.receiving_yards, s.receiving_touchdowns
        FROM player_game_stats s
        JOIN players p ON s.player_id = p.player_id
        JOIN nfl_games g ON s.game_id = g.game_id
        WHERE p.player_name ILIKE %s AND g.season = %s
        ORDER BY g.game_week
    """, (f"%{player_name}%", season))
    stats = cur.fetchall()
    cur.close()
    if not stats:
        raise HTTPException(status_code=404, detail="No stats found")
    return {"player": player_name, "season": season, "games": stats}



class TradeRequest(BaseModel):
    team_a_gives: List[str]
    team_b_gives: List[str]
    context: str = ""  # optional: e.g. "superflex league, I am rebuilding"


@app.post("/evaluate-trade")
def evaluate_trade(trade: TradeRequest):
    # Build a natural language query for the agent
    query = (
        f"Evaluate this dynasty trade. "
        f"Team A gives: {', '.join(trade.team_a_gives)}. "
        f"Team B gives: {', '.join(trade.team_b_gives)}. "
        f"Additional context: {trade.context}" if trade.context
        else
        f"Evaluate this dynasty trade. "
        f"Team A gives: {', '.join(trade.team_a_gives)}. "
        f"Team B gives: {', '.join(trade.team_b_gives)}."
    )

    try:
        analysis = evaluate_trade_with_agent(query)
        return {
            "trade": {
                "team_a_gives": trade.team_a_gives,
                "team_b_gives": trade.team_b_gives,
            },
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")